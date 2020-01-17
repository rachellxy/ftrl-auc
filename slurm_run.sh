#!/bin/bash
#SBATCH --job-name=test
#SBATCH --nodelist=ceashpc-09
#SBATCH --partition=ceashpc
#SBATCH --mem=100G
#SBATCH --ntasks=1
#SBATCH --time=96:00:00
#SBATCH --cpus-per-task=27
#SBATCH --output=/network/rit/lab/ceashpc/bz383376/git/sparse-auc/logs/re_webspam.out
/network/rit/lab/ceashpc/bz383376/opt/env-python2.7.14/bin/python data_preprocess.py