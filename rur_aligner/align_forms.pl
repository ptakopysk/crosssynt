#!/usr/bin/env perl
use strict;
use warnings;
use utf8;
use autodie;
use PerlIO::gzip;
use Getopt::Long;
use POSIX;

sub say {
    my $line = shift;
    print "$line\n";
}

sub tsvsay {
    my $line = join "\t", @_;
    print "$line\n";
}

binmode STDIN, ':utf8';
binmode STDOUT, ':utf8';
binmode STDERR, ':utf8';

my %opts = (
    'rand' => 0,
    'threshold' => 1,
    'greedy' => 0,
    'supergreedy' => 0,
    'iterations' => 1000000,
    'fert' => 1,
    'diag' => 1,
);

GetOptions(
    \%opts,
    'rand|r',
    'threshold|t=f',
    'greedy|g',
    'supergreedy|s',
    'iterations|i=i',
    'fert!',
    'diag!',
);

# A hash key for sum of counts
my $SUM = -2;

# Bucketing and upscaling constant to turn probs into ints.
# Assume max no of tokens is 10^3, so max no of links is 10^6,
# and each has a max prob of 1, so max total prob is 10^6.
# Maximal precise Perl int is > 10^15,
# so if we upscale by anything <= 10^9, we should be safe.
# (The total logprob may lose precision, but that's probably fine.)
# Currently, we upscale by 10^8.
my $BUCKETS = 100000000;

# Mix global fertility probs with word-specific ones,
# providing this many pseudo examples from the glob
# in addition to the word-specific examples.
my $GLOB_FERT_PSEUDOCOUNT = 10;

if ( @ARGV != 2 ) {
    die("Usage: $0 source.txt[.gz] target.txt[.gz] [opts] > alignment.txt \n");
}

if ($opts{rand}) {
    $opts{iterations} = 0;
}

    
warn time() . " Reading in data...\n";
sub read_in {
    my ($filename) = @_;
    warn time() . " Reading in $filename\n";
    
    my @sentences;
    my $mode = $filename =~ /\.gz$/ ? '<:gzip:utf8' : '<:utf8';
    open(my $file, $mode, $filename);
    while (my $line = <$file>) {
        chomp $line;
        my @tokens = split /[ \t]/, $line;
        push @sentences, \@tokens;
    }
    close $file;
    
    return \@sentences;
}
my $src_sentences = read_in($ARGV[0]);
my $tgt_sentences = read_in($ARGV[1]);
if (scalar(@$src_sentences) != scalar(@$tgt_sentences)) {
    die("scalar(src_sentences) != scalar(tgt_sentences)!\n");
}
warn time() . " Reading in done.\n";

my @alignments;  # alignments are 0-based
my $total_logprob = 0;

my %link_count;
my $link_count_sum;  # currently constant

my %fertility_count_src;
my %fertility_count_src_total;
my %fertility_count_tgt;
my %fertility_count_tgt_total;

# Running sum of squares of diagonalities of each link,
# for computation of diagonality variance.
# Assumes mean diagonality is 0 (this is implied by its definition),
# with a normal distribution (TODO test this part of the assumption).
# TODO also add word-specific diagonalities? These would probably require
# estimation of both mean and variance...
my $diagonality_square_sum = 0;
my $diagonality_sd = 0.1;

sub get_link_count {
    my ($sent, $src, $tgt) = @_;

    # Optimized for speed
    return $link_count{$src_sentences->[$sent]->[$src]}->{$tgt_sentences->[$sent]->[$tgt]} // 0;
}

sub set_link_count {
    my ($sent, $src, $tgt, $count) = @_;

    my $src_t = $src_sentences->[$sent]->[$src];
    my $tgt_t = $tgt_sentences->[$sent]->[$tgt];
    $link_count{$src_t}->{$tgt_t} = $count;

    return;
}

# Relative distance from the diagonal.
sub diagonality {
    my ($sent, $src, $tgt) = @_;

    my $src_len = scalar(@{$src_sentences->[$sent]});
    my $tgt_len = scalar(@{$tgt_sentences->[$sent]});
    if ($src_len == 1 || $tgt_len == 1) {
        # The diagonal is horizontal or vertical
        return 0;
    } else {
        return $src/($src_len-1) - $tgt/($tgt_len-1);
    }
}

sub toggle_fertility {
    my ($word, $fertility, $change, $is_src) = @_;

    if ($is_src) {
        $fertility_count_src{$word}->{$fertility} += $change;
        $fertility_count_src{$word}->{$SUM} += $change;
        $fertility_count_src_total{$fertility} += $change;
        $fertility_count_src_total{$SUM} += $change;
    } else {
        $fertility_count_tgt{$word}->{$fertility} += $change;
        $fertility_count_tgt{$word}->{$SUM} += $change;
        $fertility_count_tgt_total{$fertility} += $change;
        $fertility_count_tgt_total{$SUM} += $change;
    }

    return;
}

sub toggle_alignment {
    my ($sent, $change) = @_;

    my $al = $alignments[$sent];
    
    my %tgt_counted;
    foreach my $src (0..$#{$al->{src2tgt}}) {
        # Update fertility
        toggle_fertility($src_sentences->[$sent]->[$src], $al->{src_ferts}->[$src], $change, 1);
        # Get tgt
        my $tgt = $al->{src2tgt}->[$src];
        $tgt_counted{$tgt} = 1;
        # Update link count
        set_link_count($sent, $src, $tgt,
            get_link_count($sent, $src, $tgt) + $change);
        $link_count_sum += $change;
        # Update diagonality
        $diagonality_square_sum += $change * diagonality($sent, $src, $tgt)**2;
    }

    foreach my $tgt (0..$#{$al->{tgt2src}}) {
        # Update fertility
        toggle_fertility($tgt_sentences->[$sent]->[$tgt], $al->{tgt_ferts}->[$tgt], $change, 0);
        
        unless ($tgt_counted{$tgt}) {
            # Get src
            my $src = $al->{tgt2src}->[$tgt];
            # Update link count
            set_link_count($sent, $src, $tgt,
                get_link_count($sent, $src, $tgt) + $change);
            $link_count_sum += $change;
            # Update diagonality
            $diagonality_square_sum += $change * diagonality($sent, $src, $tgt)**2;
        }
    }

    # Must be non-zero
    $diagonality_sd = sqrt(1/($link_count_sum+1) * $diagonality_square_sum) + 0.1;

    return;
}

sub count_alignment {
    my ($sent) = @_;
    
    $total_logprob += $alignments[$sent]->{logprob};
    return toggle_alignment($sent, +1);
}

sub discount_alignment {
    my ($sent) = @_;

    return toggle_alignment($sent, -1);
}

my $PI = 3.14159;
my $INVs2pi = 1/sqrt(2*$PI);
sub norm_pdf {
    my ($x, $sd, $mean) = @_;
    return $INVs2pi / $sd * exp( -($x-$mean)**2 / (2*$sd**2) );
}

sub get_diag_prob {
    my ($sent, $src, $tgt) = @_;
    return norm_pdf(diagonality($sent, $src, $tgt), $diagonality_sd, 0);
}

sub get_links_rand {
    my ($sent) = @_;

    my %links;
    foreach my $src (0..$#{$src_sentences->[$sent]}) {
        foreach my $tgt (0..$#{$tgt_sentences->[$sent]}) {
            $links{$src}->{$tgt} = $BUCKETS;
            $links{$src}->{$SUM} += $BUCKETS;
        }
        $links{$SUM} += $links{$src}->{$SUM};
    }

    return \%links;
}

# Get a list of all potential links with their probabilities,
# taking into account diagonalization but not fertility
sub get_links {
    my ($sent) = @_;

    my %links;

    # First, take counts and compute sums of counts,
    # multiplied by diagonalization probability.
    my %src_sum = ();
    my %tgt_sum = ();
    foreach my $src (0..$#{$src_sentences->[$sent]}) {
        foreach my $tgt (0..$#{$tgt_sentences->[$sent]}) {
            my $count = (get_link_count($sent, $src, $tgt) + 1)
                * ($opts{diag} ? get_diag_prob($sent, $src, $tgt) : 1);
            $links{$src}->{$tgt} = $count;
            $src_sum{$src} += $count;
            $tgt_sum{$tgt} += $count;
        }
    }

    # Second, convert counts to probs:
    # p(A,B) = count(A,B) / [ count(A,*) + count(*,B) ]
    # And store sums of probs
    # To avoid rounding errors, the probs are upscaled and bucketed.
    foreach my $src (0..$#{$src_sentences->[$sent]}) {
        foreach my $tgt (0..$#{$tgt_sentences->[$sent]}) {
            $links{$src}->{$tgt} = ceil(
                $BUCKETS * $links{$src}->{$tgt}
                / ($src_sum{$src} + $tgt_sum{$tgt})
            );
            $links{$src}->{$SUM} += $links{$src}->{$tgt};
        }
        $links{$SUM} += $links{$src}->{$SUM};
    }

    return \%links;
}

# fertility_prob (= prob of increasing fertility) =
# = count(fertility > current)/sum =
# = 1 - count(fertility <= current)/sum
sub get_fert_prob {
    my ($sent, $src, $tgt, $find_src, $ferts) = @_;

    my $fert_count_word = 0;
    my $fert_count_glob = 0;
    my ($current_fert, $fert_count_glob_sum, $fert_count_word_sum);

    if ($find_src) {
        $current_fert = $ferts->[$src];
        my $word = $src_sentences->[$sent]->[$src];
        foreach my $fert (1..$current_fert) {
            $fert_count_glob += $fertility_count_src_total{$fert} // 0;
            $fert_count_word += $fertility_count_src{$word}->{$fert} // 0;
        }
        $fert_count_glob_sum = $fertility_count_src_total{$SUM} // 0;
        $fert_count_word_sum = $fertility_count_src{$word}->{$SUM} // 0;
    } else {
        $current_fert = $ferts->[$tgt];
        my $word = $tgt_sentences->[$sent]->[$tgt];
        foreach my $fert (1..$current_fert) {
            $fert_count_glob += $fertility_count_tgt_total{$fert} // 0;
            $fert_count_word += $fertility_count_tgt{$word}->{$fert} // 0;
        }
        $fert_count_glob_sum = $fertility_count_tgt_total{$SUM} // 0;
        $fert_count_word_sum = $fertility_count_tgt{$word}->{$SUM} // 0;
    }

    $fert_count_glob += $current_fert;
    $fert_count_word += $current_fert;
    $fert_count_glob_sum += $current_fert + 1;
    $fert_count_word_sum += $current_fert + 1;


    return 1 - ($fert_count_word + $GLOB_FERT_PSEUDOCOUNT*$fert_count_glob/$fert_count_glob_sum) / ($fert_count_word_sum + $GLOB_FERT_PSEUDOCOUNT);
}

sub get_uni_links_rand {
    my ($src_array, $tgt_array) = @_;
    
    my @uni_links;
    
    foreach my $src (@$src_array) {
        foreach my $tgt (@$tgt_array) {
            push @uni_links, $BUCKETS;
        }
    }
    
    return \@uni_links;
}

# Uni-directional link probs, accounting for both diagonalization and
# fertility
sub get_uni_links {
    my ($sent, $src_array, $tgt_array, $ferts, $find_src) = @_;

    my @uni_links;

    # Counts, fertilized, accounting for diagonalization probability
    my $sum = 0;
    foreach my $src (@$src_array) {
        foreach my $tgt (@$tgt_array) {
            my $count = (get_link_count($sent, $src, $tgt) + 1)
                * ($opts{fert} ? get_fert_prob($sent, $src, $tgt, $find_src, $ferts) : 1)
                * ($opts{diag} ? get_diag_prob($sent, $src, $tgt) : 1);
            push @uni_links, $count;
            $sum += $count;
        }
    }

    # Discount one-way links
    # (half of prob for each direction)
    $sum *= 2;

    # Normalize
    foreach my $item (@uni_links) {
        $item = ceil($BUCKETS * $item / $sum);
    }

    return \@uni_links;
}

sub get_src_links {
    my ($sent, $src, $tgt_ferts) = @_;

    if ($opts{rand}) {
        return get_uni_links_rand([$src], [0..$#{$tgt_sentences->[$sent]}]);
    } else {
        return get_uni_links($sent, [$src], [0..$#{$tgt_sentences->[$sent]}], $tgt_ferts, 0);
    }
}

sub get_tgt_links {
    my ($sent, $tgt, $src_ferts) = @_;
    
    if ($opts{rand}) {
        return get_uni_links_rand([0..$#{$src_sentences->[$sent]}], [$tgt]);
    } else {
        return get_uni_links($sent, [0..$#{$src_sentences->[$sent]}], [$tgt], $src_ferts, 1);
    }
}

sub sample_link {
    my ($links) = @_;

    if ($opts{supergreedy}) {
        my $best_src;
        my $best_tgt;
        my $best_prob = -1;
        foreach my $src (keys %$links) {
            next if $src == $SUM;
            foreach my $tgt (keys %{$links->{$src}}) {
                next if $tgt == $SUM;
                if ($links->{$src}->{$tgt} > $best_prob) {
                    $best_prob = $links->{$src}->{$tgt};
                    $best_src = $src;
                    $best_tgt = $tgt;
                }
            }
        }
        if (!defined $best_src) {
            die("Nothing with prob > -1 found!");
        }
        return ($best_src, $best_tgt, $best_prob/$BUCKETS);
    } else {
        my $rand = int(rand($links->{$SUM}));
        my $counter = 0;
        foreach my $src (keys %$links) {
            next if $src == $SUM;
            if ($counter + $links->{$src}->{$SUM} > $rand) {
                # The sampled link is somewhere here with this $src
                foreach my $tgt (keys %{$links->{$src}}) {
                    next if $tgt == $SUM;
                    $counter += $links->{$src}->{$tgt};
                    if ($counter > $rand) {
                        # Return the sampled link
                        return ($src, $tgt, $links->{$src}->{$tgt}/$BUCKETS);
                    }
                }
                die("$SUM key != sum of individual counts!");
            } else {
                # The sampled link is not with this $src, skip whole block
                $counter += $links->{$src}->{$SUM};
            }
        }

        die("rand(sum) >= sum! rand=$rand counter=$counter");
    }
}

sub sample_uni_link {
    my ($uni_links) = @_;

    if ($opts{supergreedy}) {
        my $best_other;
        my $best_prob = -1;
        foreach my $other (0..$#$uni_links) {
            if ($uni_links->[$other] > $best_prob) {
                $best_prob = $uni_links->[$other];
                $best_other = $other;
            }
        }
        if (!defined $best_other) {
            die("Nothing with prob > -1 found!");
        }
        return ($best_other, $best_prob/$BUCKETS);
    } else {
        my $sum = 0;
        foreach my $count (@$uni_links) {
            $sum += $count;
        }

        my $rand = int(rand($sum));
        my $counter = 0;
        foreach my $other (0..$#$uni_links) {
            $counter += $uni_links->[$other];
            if ($counter > $rand) {
                # Return the sampled link
                return ($other, $uni_links->[$other]/$BUCKETS);
            }
        }

        die("rand(sum) >= sum! sum=$sum rand=$rand counter=$counter")
    }
}

sub sample_alignment {
    my ($sent) = @_;

    my $src_tokens = $src_sentences->[$sent];
    my $src_tokens_count = scalar(@$src_tokens);
    my $tgt_tokens = $tgt_sentences->[$sent];
    my $tgt_tokens_count = scalar(@$tgt_tokens);

    # Total logprob is inaccurate in terms of fert_prob,
    # as the intersection links get fert_prob for fert=1
    # (only the last unidirectional link has the actual correct fert_prob);
    # But as this is true for all alignments,
    # and logprob is only used relatively,
    # this probably does not matter.
    # A solution would be to eventually walk over all links with fertility >1,
    # recompute their probs and update the logprob.
    
    my %alignment = (
        src2tgt => [(-1) x $src_tokens_count],
        tgt2src => [(-1) x $tgt_tokens_count],
        src_ferts => [(0) x $src_tokens_count],
        tgt_ferts => [(0) x $tgt_tokens_count],
        src2tgt_probs => [(-1) x $src_tokens_count],
        tgt2src_probs => [(-1) x $tgt_tokens_count],
        logprob => 0,
    );

    # Get all possible links
    my $links = $opts{rand} ? get_links_rand($sent) : get_links($sent);

    # Sample intersection links
    while ($links->{$SUM} > 0) {
        my ($src, $tgt, $prob) = sample_link($links);
        $links->{$SUM} -= $links->{$src}->{$SUM};
        delete $links->{$src};
        foreach my $other_src (keys %$links) {
            next if $other_src == $SUM;
            $links->{$SUM} -= $links->{$other_src}->{$tgt};
            $links->{$other_src}->{$SUM} -= $links->{$other_src}->{$tgt};
            if ($links->{$other_src}->{$SUM} == 0) {
                delete $links->{$other_src};
            } else {
                delete $links->{$other_src}->{$tgt};
            }
        }
        $alignment{src2tgt}->[$src] = $tgt;
        $alignment{tgt2src}->[$tgt] = $src;
        $alignment{src_ferts}->[$src] += 1;
        $alignment{tgt_ferts}->[$tgt] += 1;
        $alignment{src2tgt_probs}->[$src] = $prob;
        $alignment{tgt2src_probs}->[$tgt] = $prob;
        $alignment{logprob} += log($prob);  
    }

    # Sample a link for each UNALIGNED src
    foreach my $src (0..$#$src_tokens) {
        if ($alignment{src2tgt}->[$src] == -1) {
            my $src_links = get_src_links($sent, $src, $alignment{tgt_ferts});
            my ($tgt, $prob) = sample_uni_link($src_links);
            $alignment{src2tgt}->[$src] = $tgt;
            $alignment{src_ferts}->[$src] += 1;
            $alignment{tgt_ferts}->[$tgt] += 1;
            $alignment{src2tgt_probs}->[$src] = $prob;
            $alignment{logprob} += log($prob);
        }
    }

    # Sample a link for each UNALIGNED tgt
    foreach my $tgt (0..$#$tgt_tokens) {
        if ($alignment{tgt2src}->[$tgt] == -1) {
            my $tgt_links = get_tgt_links($sent, $tgt, $alignment{src_ferts});
            my ($src, $prob) = sample_uni_link($tgt_links);
            $alignment{tgt2src}->[$tgt] = $src;
            $alignment{src_ferts}->[$src] += 1;
            $alignment{tgt_ferts}->[$tgt] += 1;
            $alignment{tgt2src_probs}->[$tgt] = $prob;
            $alignment{logprob} += log($prob);
        }
    }

    # NOTE: This may be inaccurate;
    # freshly computed logprob of original alignment might be better
    if ($opts{greedy} && defined $alignments[$sent] && $alignment{logprob} < $alignments[$sent]->{logprob}) {
        return $alignments[$sent];
    } else {
        return \%alignment;
    }
}



warn time() . " Initializing...\n";
foreach my $sent (0..$#$src_sentences) {
    push @alignments, sample_alignment($sent);
    count_alignment($sent);
}
warn time() . " Initialization done (total logprob = $total_logprob).\n";

warn time() . " Resampling alignments...\n";
my $iteration = 0;
my $old_total_logprob = $total_logprob - $opts{threshold} - 1;
while ( $total_logprob - $old_total_logprob > $opts{threshold}
    && ++$iteration <= $opts{iterations}
) {
    warn time() . " Iteration $iteration...\n";
    
    $old_total_logprob = $total_logprob;
    $total_logprob = 0;
    foreach my $sent (0..$#$src_sentences) {
        discount_alignment($sent);
        $alignments[$sent] = sample_alignment($sent);
        count_alignment($sent);
    }
    
    warn time() . " Improved alignments by "
        . ($total_logprob - $old_total_logprob)
        . " (total logprob = $total_logprob).\n";
}

warn time() . " Stopping criterion met, writing out alignments...\n";
sub space_join {
    my ($arr_ref) = @_;
    return (join ' ', @$arr_ref);
}
sub add1 {
    my ($arr_ref) = @_;

    my @result = map { $_+1  } @$arr_ref;

    return \@result;
}
foreach my $sent (0..$#$src_sentences) {
    say $sent;
    say ( scalar(@{$tgt_sentences->[$sent]})
        . " "
        . space_join($tgt_sentences->[$sent])
        . "  # "
        . space_join(add1($alignments[$sent]->{tgt2src}))
        . "  # "
        . space_join($alignments[$sent]->{tgt2src_probs})
    );
    say ( scalar(@{$src_sentences->[$sent]})
        . " "
        . space_join($src_sentences->[$sent])
        . "  # "
        . space_join(add1($alignments[$sent]->{src2tgt}))
        . "  # "
        . space_join($alignments[$sent]->{src2tgt_probs})
    );
}

warn time() . " Done.\n";

