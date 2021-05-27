#!/usr/bin/python3
# *Not to be submitted*
# This scripts converts the questions on Nestor to a CSV file in the required format:
# <linenumber><tab><question>
# Author:  Jasper Bos (s3794687)
# Date:    May 27th, 2021

import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('questionfile', help='path to .txt file with all questions')
    parser.add_argument('outputfile', help='path of output file')
    args = parser.parse_args()

    count = 1
    with open(args.questionfile, 'r', encoding="utf-16") as infile, open(args.outputfile, 'w', encoding="utf-16") as outfile:
        for line in infile:
            outfile.write(str(count)+'\t'+line)
            count += 1


if __name__ == "__main__":
    main()