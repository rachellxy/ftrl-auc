# -*- coding: utf-8 -*-
import os
import sys
import time
import pickle as pkl
import multiprocessing
from os.path import join
from itertools import product

import numpy as np
from data_preprocess import data_process_01_webspam
from data_preprocess import data_process_02_news20b
from data_preprocess import data_process_03_realsim
from data_preprocess import data_process_04_avazu
from data_preprocess import data_process_05_rcv1_bin
from data_preprocess import data_process_07_url
from data_preprocess import data_process_06_pcmac
from data_preprocess import data_process_08_farmads
from data_preprocess import data_process_09_kdd2010
from data_preprocess import data_process_10_imdb
from data_preprocess import data_process_11_reviews

try:
    sys.path.append(os.getcwd())
    import sparse_module

    try:
        from sparse_module import c_algo_spam
        from sparse_module import c_algo_spauc
        from sparse_module import c_algo_solam
        from sparse_module import c_algo_fsauc
        from sparse_module import c_algo_spauc
        from sparse_module import c_algo_ftrl_auc
        from sparse_module import c_algo_ftrl_auc_hybrid
        from sparse_module import c_algo_ftrl_proximal
        from sparse_module import c_algo_rda_l1
        from sparse_module import c_algo_adagrad
    except ImportError:
        print('cannot find some function(s) in sparse_module')
        exit(0)
except ImportError:
    print('cannot find the module: sparse_module')

root_path = '/network/rit/lab/ceashpc/bz383376/data/kdd20/'


def get_from_spam_l2(dataset, num_trials):
    if os.path.exists(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, 'spam_l2')):
        results = pkl.load(open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, 'spam_l2')))
    else:
        results = []
    para_xi_list = np.zeros(num_trials)
    para_l2_list = np.zeros(num_trials)
    for result in results:
        trial_i, (para_xi, para_l2), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
        para_xi_list[trial_i] = para_xi
        para_l2_list[trial_i] = para_l2
    return para_xi_list, para_l2_list


def cv_ftrl_auc(input_para):
    data, gamma_list, para_l1_list, trial_i = input_para
    best_auc, best_para, cv_res = None, None, dict()
    para_l2, para_beta = 0.0, 1.
    for para_gamma, para_l1 in product(gamma_list, para_l1_list):
        wt, aucs, rts, iters, online_aucs, metrics = c_algo_ftrl_auc(
            data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
            data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
            data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
            data['p'], np.asarray([0, data['n'], 0], dtype=float), para_l1, para_l2, para_beta, para_gamma)
        cv_res[(trial_i, para_gamma, para_l1)] = metrics
        if best_auc is None or best_auc < metrics[0]:  # va_auc
            best_auc, best_para = metrics[0], (para_gamma, para_l1, para_l2, para_beta)
    para_gamma, para_l1, para_l2, para_beta = best_para
    wt, aucs, rts, iters, online_aucs, metrics = c_algo_ftrl_auc(
        data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
        data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
        data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
        data['p'], np.asarray([0, 100, 1], dtype=float), para_l1, para_l2, para_beta, para_gamma)
    print(para_gamma, para_l1, metrics[1])
    sys.stdout.flush()
    return trial_i, (para_gamma, para_l1), cv_res, wt, aucs, rts, iters, online_aucs, metrics


def cv_ftrl_auc_hybrid(input_para):
    data, gamma_list, para_l1_list, trial_i = input_para
    best_auc, best_para, cv_res = None, None, dict()
    para_l2, para_beta, para_k = 0.0, 1.0, 500
    for para_gamma, para_l1 in product(gamma_list, para_l1_list):
        wt, aucs, rts, iters, online_aucs, metrics = c_algo_ftrl_auc_hybrid(
            data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
            data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
            data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
            data['p'], np.asarray([0, data['n'], 0], dtype=float), para_l1, para_l2, para_beta, para_gamma, para_k)
        cv_res[(trial_i, para_gamma, para_l1)] = metrics
        if best_auc is None or best_auc < metrics[0]:  # va_auc
            best_auc, best_para = metrics[0], (para_gamma, para_l1, para_l2, para_beta)
    para_gamma, para_l1, para_l2, para_beta = best_para
    wt, aucs, rts, iters, online_aucs, metrics = c_algo_ftrl_auc_hybrid(
        data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
        data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
        data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
        data['p'], np.asarray([0, 100, 1], dtype=float), para_l1, para_l2, para_beta, para_gamma, para_k)
    print(para_gamma, para_l1, metrics[1])
    sys.stdout.flush()
    return trial_i, (para_gamma, para_l1), cv_res, wt, aucs, rts, iters, online_aucs, metrics


def cv_fsauc(input_para):
    data, para_r_list, para_g_list, trial_i = input_para
    best_auc, best_para, cv_res = None, None, dict()
    for para_r, para_g in product(para_r_list, para_g_list):
        wt, aucs, rts, iters, online_aucs, metrics = c_algo_fsauc(
            data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
            data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
            data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
            data['p'], np.asarray([0, data['n'], 0], dtype=float), para_r, para_g)
        cv_res[(trial_i, para_r, para_g)] = metrics
        if best_auc is None or best_auc < metrics[0]:  # va_auc
            best_auc, best_para = metrics[0], (para_r, para_g)
    para_r, para_g = best_para
    wt, aucs, rts, iters, online_aucs, metrics = c_algo_fsauc(
        data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
        data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
        data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
        data['p'], np.asarray([0, 100, 1], dtype=float), para_r, para_g)
    return trial_i, (para_r, para_g), cv_res, wt, aucs, rts, iters, online_aucs, metrics


def cv_spauc(input_para):
    data, para_mu_list, para_l1_list, trial_i = input_para
    best_auc, best_para, cv_res = None, None, dict()
    for para_mu, para_l1 in product(para_mu_list, para_l1_list):
        wt, aucs, rts, iters, online_aucs, metrics = c_algo_spauc(
            data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
            data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
            data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
            data['p'], np.asarray([0, data['n'], 0], dtype=float), para_mu, para_l1)
        cv_res[(trial_i, para_mu, para_l1)] = metrics
        if best_auc is None or best_auc < metrics[0]:  # va_auc
            best_auc, best_para = metrics[0], (para_mu, para_l1)
    para_mu, para_l1 = best_para
    wt, aucs, rts, iters, online_aucs, metrics = c_algo_spauc(
        data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
        data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
        data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
        data['p'], np.asarray([0, 100, 1], dtype=float), para_mu, para_l1)
    return trial_i, (para_mu, para_l1), cv_res, wt, aucs, rts, iters, online_aucs, metrics


def cv_solam(input_para):
    data, para_xi_list, para_r_list, trial_i = input_para
    best_auc, best_para, cv_res = None, None, dict()
    for para_xi, para_r in product(para_xi_list, para_r_list):
        wt, aucs, rts, iters, online_aucs, metrics = c_algo_solam(
            data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
            data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
            data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
            data['p'], np.asarray([0, data['n'], 0], dtype=float), para_xi, para_r)
        cv_res[(trial_i, para_xi, para_r)] = metrics
        if best_auc is None or best_auc < metrics[0]:  # va_auc
            best_auc, best_para = metrics[0], (para_xi, para_r)
    para_xi, para_r = best_para
    wt, aucs, rts, iters, online_aucs, metrics = c_algo_solam(
        data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
        data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
        data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
        data['p'], np.asarray([0, 100, 1], dtype=float), para_xi, para_r)
    return trial_i, (para_xi, para_r), cv_res, wt, aucs, rts, iters, online_aucs, metrics


def cv_spam_l1(input_para):
    data, para_xi_list, para_l1_list, trial_i = input_para
    best_auc, best_para, cv_res = None, None, dict()
    global_paras = np.asarray([0, data['n'], 0], dtype=float)
    for para_xi, para_l1 in product(para_xi_list, para_l1_list):
        wt, aucs, rts, iters, online_aucs, metrics = c_algo_spam(
            data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
            data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
            data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
            data['p'], global_paras, para_xi, para_l1, 0.0)
        cv_res[(trial_i, para_xi, para_l1)] = metrics
        if best_auc is None or best_auc < metrics[0]:  # va_auc
            best_auc, best_para = metrics[0], (para_xi, para_l1)
    para_xi, para_l1 = best_para
    wt, aucs, rts, iters, online_aucs, metrics = c_algo_spam(
        data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
        data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
        data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
        data['p'], np.asarray([0, 100, 1], dtype=float), para_xi, para_l1, 0.0)
    return trial_i, (para_xi, para_l1), cv_res, wt, aucs, rts, iters, online_aucs, metrics


def cv_spam_l2(input_para):
    data, para_xi_list, para_l2_list, trial_i = input_para
    best_auc, para, cv_res = None, None, dict()
    for para_xi, para_l2 in product(para_xi_list, para_l2_list):
        wt, aucs, rts, iters, online_aucs, metrics = c_algo_spam(
            data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
            data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
            data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
            data['p'], np.asarray([0, data['n'], 0], dtype=float), para_xi, 0.0, para_l2)
        cv_res[(trial_i, para_xi, para_l2)] = metrics
        if best_auc is None or best_auc < metrics[0]:  # va_auc
            best_auc, para = metrics[0], (para_xi, para_l2)
    para_xi, para_l2 = para
    wt, aucs, rts, iters, online_aucs, metrics = c_algo_spam(
        data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
        data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
        data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
        data['p'], np.asarray([0, 100, 1], dtype=float), para_xi, 0.0, para_l2)
    return trial_i, (para_xi, para_l2), cv_res, wt, aucs, rts, iters, online_aucs, metrics


def cv_spam_l1l2(input_para):
    data, para_xi_list, para_l2_list, para_l1_list, trial_i = input_para
    best_auc, best_para, cv_res = None, None, dict()
    for para_xi, para_l1, para_l2 in product(para_xi_list, para_l1_list, para_l2_list):
        wt, aucs, rts, iters, online_aucs, metrics = c_algo_spam(
            data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
            data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
            data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
            data['p'], np.asarray([0, data['n'], 0], dtype=float), para_xi, para_l1, para_l2)
        cv_res[(trial_i, para_xi, para_l1, para_l2)] = metrics
        if best_auc is None or best_auc < metrics[0]:  # va_auc
            best_auc, best_para = metrics[0], (para_xi, para_l1, para_l2)
    para_xi, para_l1, para_l2 = best_para
    wt, aucs, rts, iters, online_aucs, metrics = c_algo_spam(
        data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
        data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
        data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
        data['p'], np.asarray([0, 100, 1], dtype=float), para_xi, para_l1, para_l2)
    return trial_i, (para_xi, para_l1, para_l2), cv_res, wt, aucs, rts, iters, online_aucs, metrics


def cv_ftrl_proximal(input_para):
    data, para_gamma_list, para_l1_list, trial_i = input_para
    best_auc, best_para, cv_res = None, None, dict()
    para_l2, para_beta = 0.0, 1.0,
    for para_gamma, para_l1 in product(para_gamma_list, para_l1_list):
        wt, aucs, rts, iters, online_aucs, metrics = c_algo_ftrl_proximal(
            data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
            data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
            data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
            data['p'], np.asarray([0, data['n'], 0], dtype=float), para_l1, para_l2, para_beta, para_gamma)
        cv_res[(trial_i, para_l1, para_l2, para_beta, para_gamma)] = metrics
        if best_auc is None or best_auc < metrics[0]:  # va_auc
            best_auc, best_para = metrics[0], (para_l1, para_l2, para_beta, para_gamma)
    para_l1, para_l2, para_beta, para_gamma = best_para
    wt, aucs, rts, iters, online_aucs, metrics = c_algo_ftrl_proximal(
        data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
        data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
        data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
        data['p'], np.asarray([0, 100, 1], dtype=float), para_l1, para_l2, para_beta, para_gamma)
    sys.stdout.flush()
    return trial_i, (para_l1, para_l2, para_beta, para_gamma), cv_res, wt, aucs, rts, iters, online_aucs, metrics


def cv_rda_l1(input_para):
    data, para_lambda_list, para_gamma_list, para_rho_list, trial_i = input_para
    best_auc, para, cv_res = None, None, dict()
    for para_lambda, para_gamma, para_rho in product(para_lambda_list, para_gamma_list, para_rho_list):
        wt, aucs, rts, iters, online_aucs, metrics = c_algo_rda_l1(
            data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
            data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
            data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
            data['p'], np.asarray([0, data['n'], 0], dtype=float), para_lambda, para_gamma, para_rho)
        cv_res[(trial_i, para_lambda, para_gamma, para_rho)] = metrics
        if best_auc is None or best_auc < metrics[0]:  # va_auc
            best_auc, para = metrics[0], (para_lambda, para_gamma, para_rho)
    para_lambda, para_gamma, para_rho = para
    wt, aucs, rts, iters, online_aucs, metrics = c_algo_rda_l1(
        data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
        data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
        data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
        data['p'], np.asarray([0, 100, 1], dtype=float), para_lambda, para_gamma, para_rho)
    return trial_i, (para_lambda, para_gamma, para_rho), cv_res, wt, aucs, rts, iters, online_aucs, metrics


def cv_adagrad(input_para):
    data, para_lambda_list, para_eta_list, para_epsilon_list, trial_i = input_para
    best_auc, best_para, cv_res = None, None, dict()
    for para_lambda, para_eta, para_epsilon in product(para_lambda_list, para_eta_list, para_epsilon_list):
        wt, aucs, rts, iters, online_aucs, metrics = c_algo_adagrad(
            data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
            data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
            data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
            data['p'], np.asarray([0, data['n'], 0], dtype=float), para_lambda, para_eta, para_epsilon)
        cv_res[(trial_i, para_lambda, para_eta, para_epsilon)] = metrics
        if best_auc is None or best_auc < metrics[0]:  # va_auc
            best_auc, best_para = metrics[0], (para_lambda, para_eta, para_epsilon)
    para_lambda, para_eta, para_epsilon = best_para
    wt, aucs, rts, iters, online_aucs, metrics = c_algo_adagrad(
        data['x_tr_vals'], data['x_tr_inds'], data['x_tr_poss'], data['x_tr_lens'], data['y_tr'],
        data['trial_%d_all_indices' % trial_i], data['trial_%d_tr_indices' % trial_i],
        data['trial_%d_va_indices' % trial_i], data['trial_%d_te_indices' % trial_i],
        data['p'], np.asarray([0, 100, 1], dtype=float), para_lambda, para_eta, para_epsilon)
    return trial_i, (para_lambda, para_eta, para_epsilon), cv_res, wt, aucs, rts, iters, online_aucs, metrics


def run_high_dimensional(method, dataset, num_cpus):
    num_trials = 10
    if dataset == '02_news20b':
        data = data_process_02_news20b()
    elif dataset == '03_real_sim':
        data = data_process_03_realsim()
    elif dataset == '04_avazu':
        data = data_process_04_avazu()
    elif dataset == '05_rcv1_bin':
        data = data_process_05_rcv1_bin()
    elif dataset == '06_pcmac':
        data = data_process_06_pcmac()
    elif dataset == '07_url':
        data = data_process_07_url()
    elif dataset == '08_farmads':
        data = data_process_08_farmads()
    elif dataset == '10_imdb':
        data = data_process_10_imdb()
    elif dataset == '11_reviews':
        data = data_process_11_reviews()
    else:
        data = pkl.load(open(root_path + '%s/processed_%s.pkl' % (dataset, dataset)))
    pool = multiprocessing.Pool(processes=num_cpus)
    if method == 'ftrl_auc':
        para_gamma_list = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 5e-1, 1e0, 5e0]
        para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                        1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        para_space = [(data, para_gamma_list, para_l1_list, trial_i) for trial_i in range(num_trials)]
        ms_res = pool.map(cv_ftrl_auc, para_space)
        print(np.mean(np.asarray([_[-1][1] for _ in ms_res])))
    elif method == 'ftrl_auc_hybrid':
        para_gamma_list = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 5e-1, 1e0, 5e0]
        para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                        1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        para_space = [(data, para_gamma_list, para_l1_list, trial_i) for trial_i in range(num_trials)]
        ms_res = pool.map(cv_ftrl_auc_hybrid, para_space)
    elif method == 'spauc':
        para_mu_list = list(10. ** np.asarray([-7.0, -6.5, -6.0, -5.5, -5.0, -4.5, -4.0, -3.5, -3.0, -2.5]))
        para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                        1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        para_space = [(data, para_mu_list, para_l1_list, trial_i) for trial_i in range(num_trials)]
        ms_res = pool.map(cv_spauc, para_space)
    elif method == 'fsauc':
        para_r_list = list(10. ** np.arange(-1, 6, 1, dtype=float))
        para_g_list = list(2. ** np.arange(-10, 11, 1, dtype=float))
        para_space = [(data, para_r_list, para_g_list, trial_i) for trial_i in range(num_trials)]
        ms_res = pool.map(cv_fsauc, para_space)
    elif method == 'solam':
        para_xi_list = list(np.arange(1, 101, 9, dtype=float))
        para_r_list = list(10. ** np.arange(-1, 6, 1, dtype=float))
        para_space = [(data, para_xi_list, para_r_list, trial_i) for trial_i in range(num_trials)]
        ms_res = pool.map(cv_solam, para_space)
    elif method == 'spam_l1':
        para_xi_list = list(10. ** np.arange(-3, 4, 1, dtype=float))
        para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                        1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        para_space = [(data, para_xi_list, para_l1_list, trial_i) for trial_i in range(num_trials)]
        ms_res = pool.map(cv_spam_l1, para_space)
    elif method == 'spam_l2':
        para_xi_list = list(10. ** np.arange(-3, 4, 1, dtype=float))
        para_l2_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                        1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        para_space = [(data, para_xi_list, para_l2_list, trial_i) for trial_i in range(num_trials)]
        ms_res = pool.map(cv_spam_l2, para_space)
    elif method == 'spam_l1l2':
        para_xi_list, para_l2_list = get_from_spam_l2(dataset=dataset, num_trials=num_trials)
        para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                        1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        para_space = [(data, [para_xi_list[trial_i]], [para_l2_list[trial_i]], para_l1_list, trial_i)
                      for trial_i in range(num_trials)]
        ms_res = pool.map(cv_spam_l1l2, para_space)
    elif method == 'ftrl_proximal':
        para_gamma_list = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 5e-1, 1e0, 5e0]
        para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                        1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        para_space = [(data, para_gamma_list, para_l1_list, trial_i) for trial_i in range(num_trials)]
        ms_res = pool.map(cv_ftrl_proximal, para_space)
    elif method == 'rda_l1':
        # lambda: to control the sparsity
        para_lambda_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                            1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        # gamma: to control the learning rate. (it cannot be too small)
        para_gamma_list = [1e1, 5e1, 1e2, 5e2, 1e3, 5e3]
        # rho: to control the sparsity-enhancing parameter.
        para_rho_list = [0.0, 5e-3]
        para_space = [(data, para_lambda_list, para_gamma_list, para_rho_list, trial_i)
                      for trial_i in range(num_trials)]
        ms_res = pool.map(cv_rda_l1, para_space)
    elif method == 'adagrad':
        # lambda: to control the sparsity
        para_lambda_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                            1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        # eta: to control the learning rate. (it cannot be too small)
        para_eta_list = [1e-3, 1e-2, 1e-1, 1e0, 1e1, 5e1, 1e2, 5e2, 1e3, 5e3]
        para_epsilon_list = [1e-8]
        para_space = [(data, para_lambda_list, para_eta_list, para_epsilon_list, trial_i)
                      for trial_i in range(num_trials)]
        ms_res = pool.map(cv_adagrad, para_space)
    else:
        ms_res = None
    pool.close()
    pool.join()
    pkl.dump(ms_res, open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, method), 'wb'))


def run_huge_dimensional(method, dataset, task_id):
    if dataset == '07_url':
        data = data_process_07_url()
    elif dataset == '04_avazu':
        data = data_process_04_avazu()
    else:
        f_name = root_path + '%s/processed_%s.pkl' % (dataset, dataset)
        data = pkl.load(open(f_name))
    trial_i = int(task_id)
    if method == 'ftrl_auc':
        para_gamma_list = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 5e-1, 1e0, 5e0]
        para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                        1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        ms_res = cv_ftrl_auc((data, para_gamma_list, para_l1_list, trial_i))
    elif method == 'ftrl_proximal':
        para_gamma_list = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 5e-1, 1e0, 5e0]
        para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                        1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        ms_res = cv_ftrl_proximal((data, para_gamma_list, para_l1_list, trial_i))
    else:
        ms_res = None
    f_name = root_path + '%s/re_%s_%s_%d.pkl' % (dataset, dataset, method, task_id)
    pkl.dump(ms_res, open(f_name, 'wb'))


def result_statistics(dataset):
    aucs = []
    list_methods = ['ftrl_auc', 'spam_l1', 'spam_l2', 'spam_l1l2', 'solam', 'spauc', 'fsauc']
    list_methods = ['ftrl_auc', 'ftrl_proximal']
    for method in list_methods:
        results = pkl.load(open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, method)))
        te_auc = []
        for item in results:
            metrics = item[-1]
            te_auc.append(metrics[1])
        a = ("%0.5f" % float(np.mean(np.asarray(te_auc)))).lstrip('0')
        b = ("%0.5f" % float(np.std(np.asarray(te_auc)))).lstrip('0')
        aucs.append('$\pm$'.join([a, b]))
    print('auc: '),
    print(' & '.join(aucs))
    run_times = []
    for method in list_methods:
        results = pkl.load(open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, method)))
        run_time = []
        for item in results:
            metrics = item[-1]
            run_time.append(metrics[5])
        a = ("%0.3f" % float(np.mean(np.asarray(run_time))))
        b = ("%0.3f" % float(np.std(np.asarray(run_time))))
        run_times.append('$\pm$'.join([a, b]))
    print('run time:'),
    print(' & '.join(run_times))
    sparse_ratios = []
    for method in list_methods:
        results = pkl.load(open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, method)))
        sparse_ratio = []
        for item in results:
            metrics = item[-1]
            sparse_ratio.append(metrics[3])
        a = ("%0.4f" % float(np.mean(np.asarray(sparse_ratio)))).lstrip('0')
        b = ("%0.4f" % float(np.std(np.asarray(sparse_ratio)))).lstrip('0')
        sparse_ratios.append('$\pm$'.join([a, b]))
    print('sparse-ratio: '),
    print(' & '.join(sparse_ratios))


def result_statistics_huge(dataset='07_url'):
    aucs, num_trials = [], 1
    list_methods = ['ftrl_fast', 'ftrl_proximal']
    for method in list_methods:
        te_auc = []
        for _ in range(num_trials):
            item = pkl.load(open(root_path + '%s/re_%s_%s_%d.pkl'
                                 % (dataset, dataset, method, _)))
            metrics = item[-1]
            te_auc.append(metrics[1])
        a = ("%0.5f" % float(np.mean(np.asarray(te_auc)))).lstrip('0')
        b = ("%0.5f" % float(np.std(np.asarray(te_auc)))).lstrip('0')
        aucs.append('$\pm$'.join([a, b]))
    print(' & '.join(aucs))
    run_times = []
    for method in list_methods:
        run_time = []
        for _ in range(num_trials):
            item = pkl.load(open(root_path + '%s/re_%s_%s_%d.pkl'
                                 % (dataset, dataset, method, _)))
            metrics = item[-1]
            run_time.append(metrics[5])
        a = ("%0.3f" % float(np.mean(np.asarray(run_time))))
        b = ("%0.3f" % float(np.std(np.asarray(run_time))))
        run_times.append('$\pm$'.join([a, b]))
    print(' & '.join(run_times))
    sparse_ratios = []
    for method in list_methods:
        sparse_ratio = []
        for _ in range(num_trials):
            item = pkl.load(open(root_path + '%s/re_%s_%s_%d.pkl'
                                 % (dataset, dataset, method, _)))
            metrics = item[-1]
            sparse_ratio.append(metrics[3])
        a = ("%0.4f" % float(np.mean(np.asarray(sparse_ratio)))).lstrip('0')
        b = ("%0.4f" % float(np.std(np.asarray(sparse_ratio)))).lstrip('0')
        sparse_ratios.append('$\pm$'.join([a, b]))
    print(' & '.join(sparse_ratios))


def result_curves():
    import matplotlib.pyplot as plt
    label_method = ['FTRL-AUC', 'SPAM-L1', 'SPAM-L2', 'SPAM-L1L2', 'FSAUC', 'SOLAM']
    fig, ax = plt.subplots(1, 2)
    for ind, method in enumerate(['ftrl_auc_fast', 'spam_l1', 'spam_l2', 'spam_l1l2', 'fsauc', 'solam']):
        results = pkl.load(open(root_path + '03_real_sim/re_03_real_sim_%s.pkl' % method))
        rts_matrix, aucs_matrix = None, None
        for item in results:
            rts = item[-2]
            aucs = item[-3]
            if rts_matrix is None:
                rts_matrix = np.zeros_like(rts)
                aucs_matrix = np.zeros_like(aucs)
            rts_matrix += rts
            aucs_matrix += aucs
        rts_matrix /= float(len(results))
        aucs_matrix /= float(len(results))
        ax[0].plot(rts_matrix, aucs_matrix, label=label_method[ind])
        ax[1].plot(aucs_matrix[:100], label=label_method[ind])
    plt.legend()
    plt.show()


def result_curves_huge(dataset='07_url'):
    import matplotlib.pyplot as plt
    from matplotlib import rc
    from pylab import rcParams
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = "Times"
    plt.rcParams["font.size"] = 16
    rc('text', usetex=True)
    rcParams['figure.figsize'] = 10, 4

    label_method = ['FTRL-AUC', 'FTRL-Proximal']
    fig, ax = plt.subplots(1, 2)
    num_trials, list_trials = 5, [0, 1, 2, 3, 4, 9]
    for ind, method in enumerate(['ftrl_auc', 'ftrl_proximal']):
        results = dict()
        for _ in list_trials:
            item = pkl.load(open(root_path + '%s/re_%s_%s_%d.pkl' %
                                 (dataset, dataset, method, _)))
            results[_] = {1: item[4], 2: item[5], 3: item[6]}
        aucs = np.mean(np.asarray([results[trial_i][1] for trial_i in list_trials]), axis=0)
        aucs_std = np.std(np.asarray([results[trial_i][1] for trial_i in list_trials]), axis=0)
        rts = np.mean(np.asarray([results[trial_i][2] for trial_i in list_trials]), axis=0)
        iters = np.mean(np.asarray([results[trial_i][3] for trial_i in list_trials]), axis=0)
        print(aucs[:10], aucs_std[:10])
        ax[0].plot(rts[:40], aucs[:40], label=label_method[ind])
        ax[1].plot(iters[:40], aucs[:40], label=label_method[ind])
    ax[0].set_ylabel('AUC')
    ax[1].set_ylabel('AUC')
    ax[0].set_xlabel('Run Time(seconds)')
    ax[1].set_xlabel('Samples seen')
    ax[0].legend()
    f_name = '/home/baojian/Dropbox/Apps/ShareLaTeX/kdd20-oda-auc/figs/avazu-auc.pdf'
    plt.savefig(f_name, dpi=600, bbox_inches='tight', pad_inches=0, format='pdf')
    plt.close()


def show_parameter_select(dataset):
    import matplotlib.pyplot as plt
    from pylab import rcParams
    plt.rcParams['text.usetex'] = True
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.rcParams['text.latex.preamble'] = '\usepackage{libertine}'
    plt.rcParams["font.size"] = 14
    rcParams['figure.figsize'] = 8, 4
    list_methods = ['ftrl_auc', 'spam_l1', 'spam_l1l2', 'spauc']
    label_list = [r'FTRL-AUC', r'\textsc{SPAM}-$\displaystyle \ell^1$',
                  r'SPAM-$\displaystyle \ell^1/\ell^2$', r'SPAUC']
    marker_list = ['s', 'D', 'o', '>', '>', '<', 'v', '^']
    color_list = ['r', 'b', 'g', 'm', 'y', 'c', 'm', 'black']
    fig, ax = plt.subplots(1, 2)
    ax[0].grid(which='y', color='lightgray', linewidth=0.3, linestyle='dashed', axis='both')
    ax[1].grid(which='x', color='lightgray', linewidth=0.3, linestyle='dashed', axis='both')
    num_trials = 10
    for ind, method in enumerate(list_methods):
        print(method)
        results = pkl.load(open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, method)))
        if method == 'ftrl_auc':
            para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                            1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
            auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
            sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
            for result in results:
                trial_i, (para_gamma, para_l1), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                for ind_l1, para_l1 in enumerate(para_l1_list):
                    auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_gamma, para_l1)][1]
                    sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_gamma, para_l1)][3]
            xx = np.mean(auc_matrix, axis=0)
            yy = np.mean(sparse_ratio_mat, axis=0)
            ax[0].plot(para_l1_list, xx, marker=marker_list[ind], markersize=4.0, markerfacecolor='w',
                       markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
            ax[1].plot(xx, yy, marker=marker_list[ind], markersize=4.0, markerfacecolor='w',
                       markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
        elif method == 'spam_l1':
            para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                            1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
            auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
            sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
            for result in results:
                trial_i, (para_xi, para_l1), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                for ind_l1, para_l1 in enumerate(para_l1_list):
                    auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_l1)][1]
                    sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_l1)][3]
            xx = np.mean(auc_matrix, axis=0)
            yy = np.mean(sparse_ratio_mat, axis=0)
            ax[0].plot(para_l1_list, xx, marker=marker_list[ind], markersize=4.0, markerfacecolor='w',
                       markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
            ax[1].plot(xx, yy, marker=marker_list[ind], markersize=4.0, markerfacecolor='w',
                       markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
        elif method == 'spam_l2':
            para_l2_list = [1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
            auc_matrix = np.zeros(shape=(num_trials, len(para_l2_list)))
            sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l2_list)))
            for result in results:
                trial_i, (para_xi, para_l2), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                for ind_l1, para_l2 in enumerate(para_l2_list):
                    auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_l2)][1]
                    sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_l2)][3]
            xx = np.mean(auc_matrix, axis=0)
            yy = np.mean(sparse_ratio_mat, axis=0)
            plt.plot(xx, yy, marker=marker_list[ind], markersize=4.0, markerfacecolor='w',
                     markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
        elif method == 'spam_l1l2':
            para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                            1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
            auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
            sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
            for result in results:
                trial_i, (para_xi, para_l1, para_l2), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                for ind_l1, para_l1 in enumerate(para_l1_list):
                    auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_l1, para_l2)][1]
                    sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_l1, para_l2)][3]
            xx = np.mean(auc_matrix, axis=0)
            yy = np.mean(sparse_ratio_mat, axis=0)
            ax[0].plot(para_l1_list, xx, marker=marker_list[ind], markersize=4.0, markerfacecolor='w',
                       markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
            ax[1].plot(xx, yy, marker=marker_list[ind], markersize=4.0, markerfacecolor='w',
                       markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
        elif method == 'fsauc':
            para_r_list = 10. ** np.arange(-1, 6, 1, dtype=float)
            auc_matrix = np.zeros(shape=(num_trials, len(para_r_list)))
            sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_r_list)))
            for result in results:
                trial_i, (para_r, para_g), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                for ind_l1, para_r in enumerate(para_r_list):
                    auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_r, para_g)][1]
                    sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_r, para_g)][3]
            xx = np.mean(auc_matrix, axis=0)
            yy = np.mean(sparse_ratio_mat, axis=0)
            plt.plot(xx, yy, marker=marker_list[ind], markersize=4.0, markerfacecolor='w',
                     markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
        elif method == 'solam':
            para_r_list = 10. ** np.arange(-1, 6, 1, dtype=float)
            auc_matrix = np.zeros(shape=(num_trials, len(para_r_list)))
            sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_r_list)))
            for result in results:
                trial_i, (para_xi, para_r), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                for ind_l1, para_r in enumerate(para_r_list):
                    auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_r)][1]
                    sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_r)][3]
            xx = np.mean(auc_matrix, axis=0)
            yy = np.mean(sparse_ratio_mat, axis=0)
            plt.plot(xx, yy, marker=marker_list[ind], markersize=4.0, markerfacecolor='w',
                     markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
        elif method == 'spauc':
            para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                            1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
            auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
            sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
            for result in results:
                trial_i, (para_mu, para_l1), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                for ind_l1, para_l1 in enumerate(para_l1_list):
                    auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_mu, para_l1)][1]
                    sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_mu, para_l1)][3]
            xx = np.mean(auc_matrix, axis=0)
            yy = np.mean(sparse_ratio_mat, axis=0)
            ax[0].plot(para_l1_list, xx, marker=marker_list[ind], markersize=4.0, markerfacecolor='w',
                       markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
            ax[1].plot(xx, yy, marker=marker_list[ind], markersize=4.0, markerfacecolor='w',
                       markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
        elif method == 'rda_l1':
            lambda_list = [1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
            auc_matrix = np.zeros(shape=(num_trials, len(lambda_list)))
            sparse_ratio_mat = np.zeros(shape=(num_trials, len(lambda_list)))
            for result in results:
                trial_i, (para_lambda, para_gamma, para_rho), cv_res, wt, aucs, rts, metrics = result
                for ind_l1, para_lambda in enumerate(lambda_list):
                    auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_gamma, para_rho)][1]
                    sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_gamma, para_rho)][3]
            xx = np.mean(auc_matrix, axis=0)
            yy = np.mean(sparse_ratio_mat, axis=0)
            plt.plot(xx, yy, marker='D', label='RDA-L1')
        elif method == 'ftrl_proximal':
            para_l1_list = [1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
            auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
            sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
            for result in results:
                trial_i, (para_l1, para_l2, para_beta, para_gamma), cv_res, wt, aucs, rts, metrics = result
                for ind_l1, para_l1 in enumerate(para_l1_list):
                    auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_l1, para_l2, para_beta, para_gamma)][1]
                    sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_l1, para_l2, para_beta, para_gamma)][3]
            xx = np.mean(auc_matrix, axis=0)
            yy = np.mean(sparse_ratio_mat, axis=0)
            plt.plot(xx, yy, marker='o', label='FTRL-Proximal')
        elif method == 'adagrad':
            lambda_list = [1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
            auc_matrix = np.zeros(shape=(num_trials, len(lambda_list)))
            sparse_ratio_mat = np.zeros(shape=(num_trials, len(lambda_list)))
            for result in results:
                trial_i, (para_lambda, para_eta, para_epsilon), cv_res, wt, aucs, rts, metrics = result
                for ind_l1, para_lambda in enumerate(lambda_list):
                    auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_eta, para_epsilon)][1]
                    sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_eta, para_epsilon)][3]
            xx = np.mean(auc_matrix, axis=0)
            yy = np.mean(sparse_ratio_mat, axis=0)
            plt.plot(xx, yy, marker='o', label='AdaGrad')
    ax[0].set_ylabel('AUC')
    ax[0].set_xlabel('$\displaystyle \lambda $')
    ax[1].set_ylabel('Sparse-Ratio')
    ax[1].set_xlabel('AUC')
    ax[0].set_xscale('log')
    ax[1].set_yscale('log')
    plt.subplots_adjust(wspace=0.27, hspace=0.2)
    ax[1].legend(fancybox=True, loc='upper left', framealpha=1.0, frameon=False, borderpad=0.1,
                 labelspacing=0.2, handletextpad=0.1, markerfirst=True)
    f_name = '/home/baojian/Dropbox/Apps/ShareLaTeX/kdd20-oda-auc/figs/para-select-%s.pdf' % dataset
    plt.savefig(f_name, dpi=600, bbox_inches='tight', pad_inches=0, format='pdf')
    plt.close()


def show_auc_curves(dataset):
    import matplotlib.pyplot as plt
    from pylab import rcParams
    plt.rcParams['text.usetex'] = True
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.rcParams['text.latex.preamble'] = '\usepackage{libertine}'
    plt.rcParams["font.size"] = 14
    rcParams['figure.figsize'] = 8, 4
    list_methods = ['ftrl_auc', 'spam_l1', 'spam_l2', 'spam_l1l2', 'solam', 'spauc', 'fsauc']
    label_list = [r'FTRL-AUC', r'\textsc{SPAM}-$\displaystyle \ell^1$',
                  r'SPAM-$\displaystyle \ell^2$', r'SPAM-$\displaystyle \ell^1/\ell^2$',
                  r'SOLAM', r'SPAUC', r'FSAUC']
    list_methods = ['ftrl_auc', 'ftrl_proximal']
    label_list = [r'FTRL-AUC', r'FTRL-Proximal']
    marker_list = ['s', 'D', 'o', 'H', '>', '<', 'v', '^']
    color_list = ['r', 'b', 'g', 'gray', 'y', 'c', 'm', 'black']
    fig, ax = plt.subplots(1, 2, sharey=True)
    ax[0].grid(b=True, which='both', color='lightgray', linewidth=0.3, linestyle='dashed', axis='both')
    ax[1].grid(b=True, which='both', color='lightgray', linewidth=0.3, linestyle='dashed', axis='both')
    num_trials = 7
    for ind, method in enumerate(list_methods):
        print(method)
        results = pkl.load(open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, method)))
        aucs = np.mean(np.asarray([results[trial_i][4] for trial_i in range(num_trials)]), axis=0)
        rts = np.mean(np.asarray([results[trial_i][5] for trial_i in range(num_trials)]), axis=0)
        iters = np.mean(np.asarray([results[trial_i][6] for trial_i in range(num_trials)]), axis=0)
        ax[0].plot(rts[:20], aucs[:20], marker=marker_list[ind], markersize=3.0, markerfacecolor='w',
                   markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
        ax[1].plot(iters[:20], aucs[:20], marker=marker_list[ind], markersize=3.0, markerfacecolor='w',
                   markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
    ax[0].set_ylabel('AUC')
    ax[0].set_xlabel('Run Time')
    ax[1].set_xlabel('Samples Seen')
    # ax[0].set_xscale('log')
    # ax[1].set_xscale('log')
    for i in range(2):
        ax[i].spines['right'].set_visible(False)
        ax[i].spines['top'].set_visible(False)
    plt.subplots_adjust(wspace=0.05, hspace=0.2)
    ax[1].legend(fancybox=True, loc='lower right', framealpha=1.0,
                 bbox_to_anchor=(1.0, 0.0), frameon=False, borderpad=0.1,
                 labelspacing=0.2, handletextpad=0.1, markerfirst=True)
    f_name = '/home/baojian/Dropbox/Apps/ShareLaTeX/kdd20-oda-auc/figs/curves-%s.pdf' % dataset
    fig.savefig(f_name, dpi=600, bbox_inches='tight', pad_inches=0, format='pdf')
    plt.close()


def show_auc_curves_online(dataset):
    import matplotlib.pyplot as plt
    from pylab import rcParams
    plt.rcParams['text.usetex'] = True
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.rcParams['text.latex.preamble'] = '\usepackage{libertine}'
    plt.rcParams["font.size"] = 14
    rcParams['figure.figsize'] = 8, 4
    list_methods = ['ftrl_auc', 'spam_l1', 'spam_l2', 'spam_l1l2', 'solam', 'spauc', 'fsauc']
    label_list = [r'FTRL-AUC', r'\textsc{SPAM}-$\displaystyle \ell^1$',
                  r'SPAM-$\displaystyle \ell^2$', r'SPAM-$\displaystyle \ell^1/\ell^2$',
                  r'SOLAM', r'SPAUC', r'FSAUC']
    marker_list = ['s', 'D', 'o', 'H', '>', '<', 'v', '^']
    color_list = ['r', 'b', 'g', 'gray', 'y', 'c', 'm', 'black']
    fig, ax = plt.subplots(1, 2, sharey=True)
    ax[0].grid(b=True, which='both', color='lightgray', linewidth=0.3, linestyle='dashed', axis='both')
    ax[1].grid(b=True, which='both', color='lightgray', linewidth=0.3, linestyle='dashed', axis='both')
    num_trials = 10
    for ind, method in enumerate(list_methods):
        print(method)
        results = pkl.load(open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, method)))
        aucs = np.mean(np.asarray([results[trial_i][4] for trial_i in range(num_trials)]), axis=0)
        rts = np.mean(np.asarray([results[trial_i][5] for trial_i in range(num_trials)]), axis=0)
        iters = np.mean(np.asarray([results[trial_i][6] for trial_i in range(num_trials)]), axis=0)
        online_aucs = np.mean(np.asarray([results[trial_i][7] for trial_i in range(num_trials)]), axis=0)
        ax[0].plot(rts, online_aucs, marker=marker_list[ind], markersize=3.0, markerfacecolor='w',
                   markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
        ax[1].plot(iters, online_aucs, marker=marker_list[ind], markersize=3.0, markerfacecolor='w',
                   markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
    ax[0].set_ylabel('AUC')
    ax[0].set_xlabel('Run Time')
    ax[1].set_xlabel('Samples Seen')
    for i in range(2):
        ax[i].spines['right'].set_visible(False)
        ax[i].spines['top'].set_visible(False)
    plt.subplots_adjust(wspace=0.05, hspace=0.2)
    ax[1].legend(fancybox=True, loc='lower right', framealpha=1.0,
                 bbox_to_anchor=(1.0, 0.0), frameon=False, borderpad=0.1,
                 labelspacing=0.2, handletextpad=0.1, markerfirst=True)
    f_name = '/home/baojian/Dropbox/Apps/ShareLaTeX/kdd20-oda-auc/figs/curves-online-%s.pdf' % dataset
    fig.savefig(f_name, dpi=600, bbox_inches='tight', pad_inches=0, format='pdf')
    plt.close()


def result_all_converge_curves():
    import matplotlib.pyplot as plt
    from pylab import rcParams
    plt.rcParams['text.usetex'] = True
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.rcParams['text.latex.preamble'] = '\usepackage{libertine}'
    plt.rcParams["font.size"] = 18
    rcParams['figure.figsize'] = 16, 8.5
    list_methods = ['ftrl_auc', 'spam_l1', 'spam_l2', 'spam_l1l2', 'solam', 'spauc', 'fsauc']
    label_list = [r'FTRL-AUC', r'\textsc{SPAM}-$\displaystyle \ell^1$',
                  r'SPAM-$\displaystyle \ell^2$', r'SPAM-$\displaystyle \ell^1/\ell^2$',
                  r'SOLAM', r'SPAUC', r'FSAUC']
    marker_list = ['s', 'D', 'o', 'H', '>', '<', 'v', '^']
    color_list = ['r', 'b', 'g', 'gray', 'y', 'c', 'm', 'black']
    fig, ax = plt.subplots(2, 3)
    for i, j in product(range(2), range(3)):
        ax[i, j].grid(color='lightgray', linewidth=0.5, linestyle='dashed')
    num_trials = 10
    title_list = ['real-sim', 'farmads', 'rcv1b', 'imdb', 'reviews', 'news20b']
    for data_ind, dataset in enumerate(['03_real_sim', '08_farmads', '05_rcv1_bin',
                                        '10_imdb', '11_reviews', '02_news20b']):
        ii, jj = data_ind / 3, data_ind % 3
        for ind, method in enumerate(list_methods):
            print(method)
            results = pkl.load(open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, method)))
            aucs = np.mean(np.asarray([results[trial_i][4] for trial_i in range(num_trials)]), axis=0)
            rts = np.mean(np.asarray([results[trial_i][5] for trial_i in range(num_trials)]), axis=0)
            ax[ii, jj].plot(rts, aucs, marker=marker_list[ind], markersize=5.0, markerfacecolor='w',
                            markeredgewidth=1., linewidth=1.0, label=label_list[ind], color=color_list[ind])
        ax[ii, 0].set_ylabel('AUC')
        ax[1, jj].set_xlabel('Run Time (seconds)')
        ax[ii, jj].set_title(title_list[data_ind])
    ax[0, 0].set_ylim([0.85, 1.02])
    ax[0, 0].set_yticks([0.85, 0.90, 0.95, 1.0])
    ax[0, 0].set_yticklabels([0.85, 0.90, 0.95, 1.0])
    ax[0, 1].set_ylim([0.6, 1.02])
    ax[0, 1].set_yticks([0.6, 0.7, 0.8, 0.9, 1.0])
    ax[0, 1].set_yticklabels([0.6, 0.7, 0.8, 0.9, 1.0])
    ax[0, 2].set_ylim([0.9, 1.02])
    ax[0, 2].set_yticks([0.92, 0.94, 0.96, 0.98, 1.0])
    ax[0, 2].set_yticklabels([0.92, 0.94, 0.96, 0.98, 1.0])
    ax[1, 0].set_ylim([0.6, 1.02])
    ax[1, 0].set_yticks([0.6, 0.7, 0.8, 0.9, 1.0])
    ax[1, 0].set_yticklabels([0.6, 0.7, 0.8, 0.9, 1.0])
    ax[1, 1].set_ylim([0.6, 0.92])
    ax[1, 1].set_yticks([0.6, 0.7, 0.8, 0.9])
    ax[1, 1].set_yticklabels([0.6, 0.7, 0.8, 0.9])
    ax[1, 2].set_ylim([0.7, 1.02])
    ax[1, 2].set_yticks([0.7, 0.80, 0.90, 1.0])
    ax[1, 2].set_yticklabels([0.7, 0.80, 0.90, 1.0])
    plt.subplots_adjust(wspace=0.15, hspace=0.2)
    ax[0, 0].legend(loc='lower right', framealpha=1.0, frameon=True, borderpad=0.1,
                    labelspacing=0.2, handletextpad=0.1, markerfirst=True)
    f_name = '/home/baojian/Dropbox/Apps/ShareLaTeX/kdd20-oda-auc/figs/curves-all.pdf'
    fig.savefig(f_name, dpi=600, bbox_inches='tight', pad_inches=0, format='pdf')
    plt.close()


def result_all_converge_curves_iter():
    import matplotlib.pyplot as plt
    from pylab import rcParams
    plt.rcParams['text.usetex'] = True
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.rcParams['text.latex.preamble'] = '\usepackage{libertine}'
    plt.rcParams["font.size"] = 18
    rcParams['figure.figsize'] = 16, 8.5
    list_methods = ['ftrl_auc', 'spam_l1', 'spam_l2', 'spam_l1l2', 'solam', 'spauc', 'fsauc']
    label_list = [r'FTRL-AUC', r'\textsc{SPAM}-$\displaystyle \ell^1$',
                  r'SPAM-$\displaystyle \ell^2$', r'SPAM-$\displaystyle \ell^1/\ell^2$',
                  r'SOLAM', r'SPAUC', r'FSAUC']
    marker_list = ['s', 'D', 'o', 'H', '>', '<', 'v', '^']
    color_list = ['r', 'b', 'g', 'gray', 'y', 'c', 'm', 'black']
    fig, ax = plt.subplots(2, 3)
    for i, j in product(range(2), range(3)):
        ax[i, j].grid(color='lightgray', linewidth=0.5, linestyle='dashed')
    num_trials = 10
    title_list = ['real-sim', 'farmads', 'rcv1b', 'imdb', 'reviews', 'news20b']
    for data_ind, dataset in enumerate(['03_real_sim', '08_farmads', '05_rcv1_bin',
                                        '10_imdb', '11_reviews', '02_news20b']):
        ii, jj = data_ind / 3, data_ind % 3
        for ind, method in enumerate(list_methods):
            print(method)
            results = pkl.load(open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, method)))
            aucs = np.mean(np.asarray([results[trial_i][4] for trial_i in range(num_trials)]), axis=0)
            iters = np.mean(np.asarray([results[trial_i][6] for trial_i in range(num_trials)]), axis=0)
            ax[ii, jj].plot(iters, aucs, marker=marker_list[ind], markersize=5.0, markerfacecolor='w',
                            markeredgewidth=1., linewidth=1.0, label=label_list[ind], color=color_list[ind])
        ax[ii, 0].set_ylabel('AUC')
        ax[1, jj].set_xlabel('Run Time (seconds)')
        ax[ii, jj].set_title(title_list[data_ind])
    ax[0, 0].set_ylim([0.85, 1.02])
    ax[0, 0].set_yticks([0.85, 0.90, 0.95, 1.0])
    ax[0, 0].set_yticklabels([0.85, 0.90, 0.95, 1.0])
    ax[0, 1].set_ylim([0.6, 1.02])
    ax[0, 1].set_yticks([0.6, 0.7, 0.8, 0.9, 1.0])
    ax[0, 1].set_yticklabels([0.6, 0.7, 0.8, 0.9, 1.0])
    ax[0, 2].set_ylim([0.9, 1.02])
    ax[0, 2].set_yticks([0.92, 0.94, 0.96, 0.98, 1.0])
    ax[0, 2].set_yticklabels([0.92, 0.94, 0.96, 0.98, 1.0])
    ax[1, 0].set_ylim([0.6, 1.02])
    ax[1, 0].set_yticks([0.6, 0.7, 0.8, 0.9, 1.0])
    ax[1, 0].set_yticklabels([0.6, 0.7, 0.8, 0.9, 1.0])
    ax[1, 1].set_ylim([0.6, 0.92])
    ax[1, 1].set_yticks([0.6, 0.7, 0.8, 0.9])
    ax[1, 1].set_yticklabels([0.6, 0.7, 0.8, 0.9])
    ax[1, 2].set_ylim([0.7, 1.02])
    ax[1, 2].set_yticks([0.7, 0.80, 0.90, 1.0])
    ax[1, 2].set_yticklabels([0.7, 0.80, 0.90, 1.0])
    plt.subplots_adjust(wspace=0.15, hspace=0.2)
    ax[1, 1].legend(loc='lower center', framealpha=1.0, frameon=True, borderpad=0.1,
                    labelspacing=0.2, handletextpad=0.1, markerfirst=True)
    f_name = '/home/baojian/Dropbox/Apps/ShareLaTeX/kdd20-oda-auc/figs/curves-all-iter.pdf'
    fig.savefig(f_name, dpi=600, bbox_inches='tight', pad_inches=0, format='pdf')
    plt.close()


def show_all_parameter_select():
    import matplotlib.pyplot as plt
    from pylab import rcParams
    plt.rcParams['text.usetex'] = True
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.rcParams['text.latex.preamble'] = '\usepackage{libertine}'
    plt.rcParams["font.size"] = 18
    rcParams['figure.figsize'] = 16, 8.5
    list_methods = ['ftrl_auc', 'spam_l1', 'spam_l1l2', 'spauc']
    label_list = [r'FTRL-AUC', r'\textsc{SPAM}-$\displaystyle \ell^1$',
                  r'SPAM-$\displaystyle \ell^1/\ell^2$', r'SPAUC']
    marker_list = ['s', 'D', 'o', '>', '>', '<', 'v', '^']
    color_list = ['r', 'b', 'g', 'm', 'y', 'c', 'm', 'black']
    fig, ax = plt.subplots(2, 3)
    for i, j in product(range(2), range(3)):
        ax[i, j].grid(color='lightgray', linewidth=0.5, linestyle='dashed')
    num_trials = 10
    title_list = ['real-sim', 'farmads', 'rcv1b', 'imdb', 'reviews', 'news20b']
    for data_ind, dataset in enumerate(['03_real_sim', '08_farmads', '05_rcv1_bin',
                                        '10_imdb', '11_reviews', '02_news20b']):
        ii, jj = data_ind / 3, data_ind % 3
        for ind, method in enumerate(list_methods):
            print(method)
            results = pkl.load(open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, method)))
            if method == 'ftrl_auc':
                para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                                1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
                auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
                sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
                for result in results:
                    trial_i, (para_gamma, para_l1), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                    for ind_l1, para_l1 in enumerate(para_l1_list):
                        auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_gamma, para_l1)][1]
                        sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_gamma, para_l1)][3]
                xx = np.mean(auc_matrix, axis=0)
                yy = np.mean(sparse_ratio_mat, axis=0)
            elif method == 'spam_l1':
                para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                                1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
                auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
                sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
                for result in results:
                    trial_i, (para_xi, para_l1), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                    for ind_l1, para_l1 in enumerate(para_l1_list):
                        auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_l1)][1]
                        sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_l1)][3]
                xx = np.mean(auc_matrix, axis=0)
                yy = np.mean(sparse_ratio_mat, axis=0)
            elif method == 'spam_l1l2':
                para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                                1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
                auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
                sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
                for result in results:
                    trial_i, (para_xi, para_l1, para_l2), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                    for ind_l1, para_l1 in enumerate(para_l1_list):
                        auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_l1, para_l2)][1]
                        sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_xi, para_l1, para_l2)][3]
                xx = np.mean(auc_matrix, axis=0)
                yy = np.mean(sparse_ratio_mat, axis=0)
            else:  # spauc
                para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                                1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
                auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
                sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
                for result in results:
                    trial_i, (para_mu, para_l1), cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                    for ind_l1, para_l1 in enumerate(para_l1_list):
                        auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_mu, para_l1)][1]
                        sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_mu, para_l1)][3]
                xx = np.mean(auc_matrix, axis=0)
                yy = np.mean(sparse_ratio_mat, axis=0)
            ax[ii, jj].plot(xx, yy, marker=marker_list[ind], markersize=6.0, markerfacecolor='w',
                            markeredgewidth=1.5, linewidth=1.5, label=label_list[ind], color=color_list[ind])
            ax[ii, 0].set_ylabel('Sparse-Ratio')
            ax[1, jj].set_xlabel('AUC')
            ax[ii, jj].set_yscale('log')
            ax[ii, jj].set_title(title_list[data_ind])
    plt.subplots_adjust(wspace=0.15, hspace=0.2)
    ax[0, 0].legend(fancybox=True, loc='upper left', framealpha=1.0, frameon=True, borderpad=0.1,
                    labelspacing=0.2, handletextpad=0.1, markerfirst=True)
    f_name = '/home/baojian/Dropbox/Apps/ShareLaTeX/kdd20-oda-auc/figs/para-select-all.pdf'
    plt.savefig(f_name, dpi=600, bbox_inches='tight', pad_inches=0, format='pdf')
    plt.close()


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run_high_dimensional(method=sys.argv[2],
                             dataset=sys.argv[3],
                             num_cpus=int(sys.argv[4]))
    elif sys.argv[1] == 'run_huge':
        run_huge_dimensional(method=sys.argv[2],
                             dataset=sys.argv[3],
                             task_id=int(sys.argv[4]))
    elif sys.argv[1] == 'run_merge':
        dataset = sys.argv[2]
        for method in ['ftrl_auc', 'ftrl_proximal']:
            all_res = []
            for i in range(10):
                re = pkl.load(open(root_path + '%s/re_%s_%s_%d.pkl' % (dataset, dataset, method, i)))
                all_res.append(re)
            pkl.dump(all_res, open(root_path + '%s/re_%s_%s.pkl' % (dataset, dataset, method), 'wb'))
    elif sys.argv[1] == 'show_auc':
        result_statistics(dataset=sys.argv[2])
    elif sys.argv[1] == 'show_auc_curves':
        show_auc_curves(dataset=sys.argv[2])
    elif sys.argv[1] == 'show_auc_curves_online':
        show_auc_curves_online(dataset=sys.argv[2])
    elif sys.argv[1] == 'show_para_select':
        show_parameter_select(dataset=sys.argv[2])
    elif sys.argv[1] == 'show_auc_huge':
        result_statistics_huge(dataset=sys.argv[2])
    elif sys.argv[1] == 'show_curves_huge':
        result_curves_huge(dataset=sys.argv[2])
    elif sys.argv[1] == 'all_converge_curves':
        result_all_converge_curves()
    elif sys.argv[1] == 'all_converge_curves_iter':
        result_all_converge_curves_iter()
    elif sys.argv[1] == 'all_para_select':
        show_all_parameter_select()
