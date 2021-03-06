# -*- coding: utf-8 -*-
import os
import sys
import time
import pickle as pkl
import multiprocessing
from os.path import join
from itertools import product

import numpy as np
from data_preprocess import data_process_01_news20b
from data_preprocess import data_process_02_realsim
from data_preprocess import data_process_03_rcv1_bin
from data_preprocess import data_process_04_farmads
from data_preprocess import data_process_05_imdb
from data_preprocess import data_process_06_reviews
from data_preprocess import data_process_07_avazu

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
        from sparse_module import c_algo_ftrl_proximal
        from sparse_module import c_algo_rda_l1
        from sparse_module import c_algo_adagrad
    except ImportError:
        print('cannot find some function(s) in sparse_module')
        exit(0)
except ImportError:
    print('cannot find the module: sparse_module')

root_path = '--- configure your path ---'


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
    print('test')
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


def get_imbalance_data(data, imbalance_ratio=0.1, num_trials=10):
    data['num_posi'] = int(imbalance_ratio * data['num_nega'])
    cur_posi = 0
    y_tr = []
    x_tr_vals = []
    x_tr_inds = []
    x_tr_poss = []
    x_tr_lens = []
    index_posi = 0
    for sample_i in range(data['n']):
        cur_len = data['x_tr_lens'][sample_i]
        cur_poss = data['x_tr_poss'][sample_i]
        cur_inds = data['x_tr_inds'][cur_poss:cur_poss + cur_len]
        cur_values = data['x_tr_vals'][cur_poss:cur_poss + cur_len]
        if data['y_tr'][sample_i] > 0 and cur_posi < data['num_posi']:
            x_tr_inds.extend(cur_inds)
            x_tr_vals.extend(cur_values)
            x_tr_poss.append(index_posi)
            index_posi += cur_len
            x_tr_lens.append(cur_len)
            y_tr.append(1)
            cur_posi += 1
        elif data['y_tr'][sample_i] > 0 and cur_posi >= data['num_posi']:
            pass
        else:
            x_tr_inds.extend(cur_inds)
            x_tr_vals.extend(cur_values)
            x_tr_poss.append(index_posi)
            index_posi += cur_len
            x_tr_lens.append(cur_len)
            y_tr.append(-1)

    data['n'] = data['num_posi'] + data['num_nega']
    data['x_tr_vals'] = np.asarray(x_tr_vals, dtype=float)
    data['x_tr_inds'] = np.asarray(x_tr_inds, dtype=np.int32)
    data['x_tr_lens'] = np.asarray(x_tr_lens, dtype=np.int32)
    data['x_tr_poss'] = np.asarray(x_tr_poss, dtype=np.int32)
    data['y_tr'] = np.asarray(y_tr, dtype=float)
    data['n'] = len(y_tr)
    data['p'] = data['p']

    data['k'] = np.ceil(len(data['x_tr_vals']) / float(data['n']))
    assert len(np.unique(data['y_tr'])) == 2  # we have total 2 classes.
    data['num_posi'] = len([_ for _ in data['y_tr'] if _ > 0])
    data['num_nega'] = len([_ for _ in data['y_tr'] if _ < 0])
    data['posi_ratio'] = float(data['num_posi']) / float(data['num_nega'])
    data['num_nonzeros'] = len(data['x_tr_vals'])
    print('number of positive: %d' % len([_ for _ in data['y_tr'] if _ > 0]))
    print('number of negative: %d' % len([_ for _ in data['y_tr'] if _ < 0]))
    print('number of num_nonzeros: %d' % data['num_nonzeros'])
    print('k: %d' % data['k'])
    for _ in range(num_trials):
        all_indices = np.random.permutation(data['n'])
        print(all_indices[:5])
        data['trial_%d_all_indices' % _] = np.asarray(all_indices, dtype=np.int32)
        assert data['n'] == len(data['trial_%d_all_indices' % _])
        tr_indices = all_indices[:int(len(all_indices) * 4. / 6.)]
        data['trial_%d_tr_indices' % _] = np.asarray(tr_indices, dtype=np.int32)
        va_indices = all_indices[int(len(all_indices) * 4. / 6.):int(len(all_indices) * 5. / 6.)]
        data['trial_%d_va_indices' % _] = np.asarray(va_indices, dtype=np.int32)
        te_indices = all_indices[int(len(all_indices) * 5. / 6.):]
        data['trial_%d_te_indices' % _] = np.asarray(te_indices, dtype=np.int32)
        n_tr = len(data['trial_%d_tr_indices' % _])
        n_va = len(data['trial_%d_va_indices' % _])
        n_te = len(data['trial_%d_te_indices' % _])
        assert data['n'] == (n_tr + n_va + n_te)
    sys.stdout.flush()
    return data


def run_high_dimensional(method, dataset, num_cpus):
    num_trials, imbalance_ratio = 10, 0.05
    if dataset == '02_news20b':
        data = data_process_01_news20b()
    elif dataset == '03_real_sim':
        data = data_process_02_realsim()
    elif dataset == '05_rcv1_bin':
        data = data_process_03_rcv1_bin()
    elif dataset == '06_pcmac':
        data = data_process_06_pcmac()
    elif dataset == '08_farmads':
        data = data_process_04_farmads()
    elif dataset == '10_imdb':
        data = data_process_05_imdb()
    elif dataset == '11_reviews':
        data = data_process_06_reviews()
    else:
        data = None
    data = get_imbalance_data(data, imbalance_ratio=imbalance_ratio, num_trials=num_trials)
    pool = multiprocessing.Pool(processes=num_cpus)
    if method == 'ftrl_auc':
        para_gamma_list = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 5e-1, 1e0, 5e0]
        para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                        1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        para_space = [(data, para_gamma_list, para_l1_list, trial_i) for trial_i in range(num_trials)]
        ms_res = pool.map(cv_ftrl_auc, para_space)
        print(np.mean(np.asarray([_[-1][1] for _ in ms_res])))
    elif method == 'ftrl_proximal':
        para_gamma_list = [1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1, 5e-1, 1e0, 5e0]
        para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                        1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
        para_space = [(data, para_gamma_list, para_l1_list, trial_i) for trial_i in range(num_trials)]
        ms_res = pool.map(cv_ftrl_proximal, para_space)
        print(np.mean(np.asarray([_[-1][1] for _ in ms_res])))
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
    pkl.dump(ms_res, open(root_path + '%s/re_%s_%s_imbalance_%.2f.pkl' %
                          (dataset, dataset, method, imbalance_ratio), 'wb'))


def run_huge_dimensional(method, dataset, task_id):
    if dataset == '07_url':
        data = data_process_07_url()
    elif dataset == '01_webspam':
        data = data_process_01_webspam()
    elif dataset == '04_avazu':
        data = data_process_07_avazu()
    elif dataset == '09_kdd2010':
        data = data_process_09_kdd2010()
    else:
        f_name = root_path + '%s/processed_%s.pkl' % (dataset, dataset)
        data = pkl.load(open(f_name))
    trial_i = int(task_id)
    if method == 'ftrl_auc':
        ms_res = cv_ftrl_auc((data, trial_i))
    elif method == 'ftrl_proximal':
        ms_res = cv_ftrl_proximal((data, trial_i))
    else:
        ms_res = None
    f_name = root_path + '%s/re_%s_%s_%d.pkl' % (dataset, dataset, method, task_id)
    pkl.dump(ms_res, open(f_name, 'wb'))


def result_statistics(dataset, imbalance_ratio=0.1):
    aucs = []
    list_methods = ['ftrl_auc', 'adagrad', 'rda_l1', 'ftrl_proximal']
    for method in list_methods:
        results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_%.2f.pkl' %
                                (dataset, dataset, method, imbalance_ratio)))
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
        results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_%.2f.pkl' %
                                (dataset, dataset, method, imbalance_ratio)))
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
        results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_%.2f.pkl' %
                                (dataset, dataset, method, imbalance_ratio)))
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

    label_method = [r'\textsc{FTRL-AUC}', r'\textsc{FTRL-Pro}']
    fig, ax = plt.subplots(1, 2)
    num_trials = 1
    for ind, method in enumerate(['ftrl_fast', 'ftrl_proximal']):
        rts_matrix, aucs_matrix = None, None
        for _ in range(num_trials):
            item = pkl.load(open(root_path + '%s/re_%s_%s_%d.pkl' %
                                 (dataset, dataset, method, _)))
            rts = item[-2]
            aucs = item[-3]
            if rts_matrix is None:
                rts_matrix = np.zeros_like(rts)
                aucs_matrix = np.zeros_like(aucs)
            rts_matrix += rts
            aucs_matrix += aucs
        rts_matrix /= float(num_trials)
        aucs_matrix /= float(num_trials)
        print(len(rts_matrix), len(aucs_matrix))
        ax[0].plot(rts_matrix[:200], aucs_matrix[:200], label=label_method[ind])
        ax[1].plot(aucs_matrix[:200], label=label_method[ind])
    ax[0].set_ylabel('AUC')
    ax[1].set_ylabel('AUC')
    ax[0].set_xlabel('Run Time(seconds)')
    ax[1].set_xlabel('Iteration * $\displaystyle 10^{4}$')
    ax[0].legend()
    f_name = '--- config your path ---/avazu-auc.pdf'
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
    f_name = '--- config your path ---/para-select-%s.pdf' % dataset
    plt.savefig(f_name, dpi=600, bbox_inches='tight', pad_inches=0, format='pdf')
    plt.close()


def show_auc_curves(dataset, imbalance_ratio=0.1):
    import matplotlib.pyplot as plt
    from pylab import rcParams
    plt.rcParams['text.usetex'] = True
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.rcParams['text.latex.preamble'] = '\usepackage{libertine}'
    plt.rcParams["font.size"] = 14
    rcParams['figure.figsize'] = 8, 4
    list_methods = ['ftrl_auc', 'adagrad', 'rda_l1', 'ftrl_proximal']
    label_list = [r'FTRL-AUC', r'\textsc{AdaGrad}',
                  r'RDA-$\displaystyle \ell^1$', r'FTRL-Proximal']
    marker_list = ['s', 'D', 'o', 'H', '>', '<', 'v', '^']
    color_list = ['r', 'b', 'g', 'gray', 'y', 'c', 'm', 'black']
    fig, ax = plt.subplots(1, 2, sharey=True)
    ax[0].grid(b=True, which='both', color='lightgray', linewidth=0.3, linestyle='dashed', axis='both')
    ax[1].grid(b=True, which='both', color='lightgray', linewidth=0.3, linestyle='dashed', axis='both')
    num_trials = 10
    for ind, method in enumerate(list_methods):
        print(method)
        results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_%.1f.pkl' %
                                (dataset, dataset, method, imbalance_ratio)))
        aucs = np.mean(np.asarray([results[trial_i][4] for trial_i in range(num_trials)]), axis=0)
        rts = np.mean(np.asarray([results[trial_i][5] for trial_i in range(num_trials)]), axis=0)
        iters = np.mean(np.asarray([results[trial_i][6] for trial_i in range(num_trials)]), axis=0)
        ax[0].plot(rts, aucs, marker=marker_list[ind], markersize=3.0, markerfacecolor='w',
                   markeredgewidth=.7, linewidth=0.5, label=label_list[ind], color=color_list[ind])
        ax[1].plot(iters, aucs, marker=marker_list[ind], markersize=3.0, markerfacecolor='w',
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
    f_name = '--- config your path ---/curves-%s-imbalance_%.1f.pdf' % \
             (dataset, imbalance_ratio)
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
    f_name = '--- config your path ---/curves-online-%s.pdf' % dataset
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
    imbalance_ratio = 0.1
    list_methods = ['ftrl_auc', 'adagrad', 'rda_l1', 'ftrl_proximal']
    label_list = [r'FTRL-AUC', r'\textsc{AdaGrad}', r'RDA-$\displaystyle \ell^1$', r'FTRL-Proximal']
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
            results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_%.1f.pkl'
                                    % (dataset, dataset, method, imbalance_ratio)))
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
    f_name = '--- config your path ---/curves-all-imbalance-%.2f.pdf' % imbalance_ratio
    fig.savefig(f_name, dpi=600, bbox_inches='tight', pad_inches=0, format='pdf')
    plt.close()


def get_data_fig6():
    path = '--- config your path ---'
    num_trials = 10
    data_fig6 = dict()
    list_methods = ['ftrl_auc', 'adagrad', 'rda_l1', 'ftrl_proximal']
    for data_ind, dataset in enumerate(['03_real_sim', '08_farmads', '05_rcv1_bin',
                                        '10_imdb', '11_reviews', '02_news20b']):
        data_fig6[dataset] = dict()
        ii, jj = data_ind / 3, data_ind % 3
        data_fig6[dataset][(ii, jj)] = dict()
        for ind, method in enumerate(list_methods):
            print(dataset, method)
            results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_0.1.pkl' % (dataset, dataset, method)))
            aucs = np.mean(np.asarray([results[trial_i][4] for trial_i in range(num_trials)]), axis=0)
            rts = np.mean(np.asarray([results[trial_i][6] for trial_i in range(num_trials)]), axis=0)
            data_fig6[dataset][(ii, jj)][method] = [rts, aucs]
    pkl.dump(data_fig6, open(path + '/results/data_fig6.pkl', 'wb'))
    exit()


def get_data_fig5():
    path = '--- config your path ---'
    list_methods = ['ftrl_auc', 'adagrad', 'rda_l1', 'ftrl_proximal']
    num_trials = 10
    imbalance_ratio = 0.1
    data_fig5 = dict()
    for data_ind, dataset in enumerate(['03_real_sim', '08_farmads', '05_rcv1_bin',
                                        '10_imdb', '11_reviews', '02_news20b']):
        data_fig5[dataset] = dict()
        ii, jj = data_ind / 3, data_ind % 3
        data_fig5[dataset][(ii, jj)] = dict()
        for ind, method in enumerate(list_methods):
            print(dataset, method)
            results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_%0.1f.pkl' %
                                    (dataset, dataset, method, imbalance_ratio)))
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
            elif method == 'adagrad':
                para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                                1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
                auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
                sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
                for result in results:
                    trial_i, (para_lambda, para_eta, para_epsilon), \
                    cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                    for ind_l1, para_lambda in enumerate(para_l1_list):
                        auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_eta, para_epsilon)][1]
                        sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_eta, para_epsilon)][3]
                xx = np.mean(auc_matrix, axis=0)
                yy = np.mean(sparse_ratio_mat, axis=0)
            elif method == 'rda_l1':
                para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                                1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
                auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
                sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
                for result in results:
                    trial_i, (para_lambda, para_gamma, para_rho), \
                    cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                    for ind_l1, para_lambda in enumerate(para_l1_list):
                        auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_gamma, para_rho)][1]
                        sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_gamma, para_rho)][3]
                xx = np.mean(auc_matrix, axis=0)
                yy = np.mean(sparse_ratio_mat, axis=0)
            else:  # ftrl_proximal
                para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                                1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
                auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
                sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
                for result in results:
                    trial_i, (para_l1, para_l2, para_beta, para_gamma), \
                    cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                    for ind_l1, para_l1 in enumerate(para_l1_list):
                        auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_l1, para_l2, para_beta, para_gamma)][1]
                        sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_l1, para_l2, para_beta, para_gamma)][
                            3]
                xx = np.mean(auc_matrix, axis=0)
                yy = np.mean(sparse_ratio_mat, axis=0)
            data_fig5[dataset][(ii, jj)][method] = [xx, yy]
    pkl.dump(data_fig5, open(path + '/results/data_fig5.pkl', 'wb'))
    exit()


def get_data_fig10():
    path = '--- config your path ---'
    list_methods = ['ftrl_auc', 'adagrad', 'rda_l1', 'ftrl_proximal']
    num_trials = 10
    imbalance_ratio = 0.05
    data_fig5 = dict()
    for data_ind, dataset in enumerate(['03_real_sim', '08_farmads', '05_rcv1_bin',
                                        '10_imdb', '11_reviews', '02_news20b']):
        data_fig5[dataset] = dict()
        ii, jj = data_ind / 3, data_ind % 3
        data_fig5[dataset][(ii, jj)] = dict()
        for ind, method in enumerate(list_methods):
            print(dataset, method)
            results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_%0.1f.pkl' %
                                    (dataset, dataset, method, imbalance_ratio)))
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
            elif method == 'adagrad':
                para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                                1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
                auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
                sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
                for result in results:
                    trial_i, (para_lambda, para_eta, para_epsilon), \
                    cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                    for ind_l1, para_lambda in enumerate(para_l1_list):
                        auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_eta, para_epsilon)][1]
                        sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_eta, para_epsilon)][3]
                xx = np.mean(auc_matrix, axis=0)
                yy = np.mean(sparse_ratio_mat, axis=0)
            elif method == 'rda_l1':
                para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                                1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
                auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
                sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
                for result in results:
                    trial_i, (para_lambda, para_gamma, para_rho), \
                    cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                    for ind_l1, para_lambda in enumerate(para_l1_list):
                        auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_gamma, para_rho)][1]
                        sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_lambda, para_gamma, para_rho)][3]
                xx = np.mean(auc_matrix, axis=0)
                yy = np.mean(sparse_ratio_mat, axis=0)
            else:  # ftrl_proximal
                para_l1_list = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2,
                                1e-1, 3e-1, 5e-1, 7e-1, 1e0, 3e0, 5e0]
                auc_matrix = np.zeros(shape=(num_trials, len(para_l1_list)))
                sparse_ratio_mat = np.zeros(shape=(num_trials, len(para_l1_list)))
                for result in results:
                    trial_i, (para_l1, para_l2, para_beta, para_gamma), \
                    cv_res, wt, aucs, rts, iters, online_aucs, metrics = result
                    for ind_l1, para_l1 in enumerate(para_l1_list):
                        auc_matrix[trial_i][ind_l1] = cv_res[(trial_i, para_l1, para_l2, para_beta, para_gamma)][1]
                        sparse_ratio_mat[trial_i][ind_l1] = cv_res[(trial_i, para_l1, para_l2, para_beta, para_gamma)][
                            3]
                xx = np.mean(auc_matrix, axis=0)
                yy = np.mean(sparse_ratio_mat, axis=0)
            data_fig5[dataset][(ii, jj)][method] = [xx, yy]
    pkl.dump(data_fig5, open(path + '/results/data_fig10.pkl', 'wb'))
    exit()


def get_data_fig11():
    path = '--- config your path ---'
    num_trials = 10
    data_fig6 = dict()
    list_methods = ['ftrl_auc', 'adagrad', 'rda_l1', 'ftrl_proximal']
    for data_ind, dataset in enumerate(['03_real_sim', '08_farmads', '05_rcv1_bin',
                                        '10_imdb', '11_reviews', '02_news20b']):
        data_fig6[dataset] = dict()
        ii, jj = data_ind / 3, data_ind % 3
        data_fig6[dataset][(ii, jj)] = dict()
        for ind, method in enumerate(list_methods):
            print(dataset, method)
            results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_0.05.pkl' % (dataset, dataset, method)))
            aucs = np.mean(np.asarray([results[trial_i][4] for trial_i in range(num_trials)]), axis=0)
            rts = np.mean(np.asarray([results[trial_i][6] for trial_i in range(num_trials)]), axis=0)
            data_fig6[dataset][(ii, jj)][method] = [rts, aucs]
    pkl.dump(data_fig6, open(path + '/results/data_fig11.pkl', 'wb'))
    exit()


def result_all_converge_curves_iter():
    import matplotlib.pyplot as plt
    from pylab import rcParams
    plt.rcParams['text.usetex'] = True
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.rcParams['text.latex.preamble'] = '\usepackage{libertine}'
    plt.rcParams["font.size"] = 20
    rcParams['figure.figsize'] = 12, 7
    list_methods = ['ftrl_auc', 'adagrad', 'rda_l1', 'ftrl_proximal']
    label_list = [r'FTRL-AUC', r'\textsc{AdaGrad}', r'RDA-$\displaystyle \ell^1$', r'\textsc{FTRL-Pro}']
    marker_list = ['s', 'D', 'o', 'H', '>', '<', 'v', '^']
    color_list = ['r', 'b', 'g', 'gray', 'y', 'c', 'm', 'black']
    fig, ax = plt.subplots(2, 3)
    for i, j in product(range(2), range(3)):
        ax[i, j].grid(color='gray', linewidth=0.5, linestyle='--', dashes=(10, 10))
        ax[i, j].spines['right'].set_visible(False)
        ax[i, j].spines['top'].set_visible(False)
    data_fig6 = pkl.load(open('--- config your path ---/results/data_fig11.pkl'))
    title_list = ['(a) real-sim', '(b) farm-ads', '(c) rcv1b', '(d) imdb', '(e) reviews', '(f) news20b']
    for data_ind, dataset in enumerate(['03_real_sim', '08_farmads', '05_rcv1_bin',
                                        '10_imdb', '11_reviews', '02_news20b']):
        ii, jj = data_ind / 3, data_ind % 3
        for ind, method in enumerate(list_methods):
            iters, aucs = data_fig6[dataset][(ii, jj)][method]
            ax[ii, jj].plot(iters, aucs, marker=marker_list[ind], markersize=5.0, markerfacecolor='w',
                            markeredgewidth=1., linewidth=1.0, label=label_list[ind], color=color_list[ind])
        ax[ii, 0].set_ylabel('AUC')
        ax[1, jj].set_xlabel('Samples Seen')
        ax[ii, jj].set_title(title_list[data_ind])
    ax[0, 0].set_ylim([0.76, 1.01])
    ax[0, 0].set_yticks([0.82, 0.88, 0.94])
    ax[0, 0].set_yticklabels([0.82, 0.88, 0.94])
    ax[0, 0].set_xticks([10000, 20000, 30000])
    ax[0, 0].set_xticklabels([10000, 20000, 30000])

    ax[0, 1].set_ylim([0.55, 0.95])
    ax[0, 1].set_yticks([0.65, 0.75, 0.85])
    ax[0, 1].set_yticklabels([0.65, 0.75, 0.85])
    ax[0, 1].set_xticks([400, 800, 1200])
    ax[0, 1].set_xticklabels([400, 800, 1200])

    ax[0, 2].set_ylim([0.76, 1.01])
    ax[0, 2].set_yticks([0.82, 0.88, 0.94])
    ax[0, 2].set_yticklabels([0.82, 0.88, 0.94])
    ax[0, 2].set_xticks([40000, 120000, 200000])
    ax[0, 2].set_xticklabels([40000, 120000, 200000])

    ax[1, 0].set_ylim([0.55, 0.95])
    ax[1, 0].set_yticks([0.65, 0.75, 0.85])
    ax[1, 0].set_yticklabels([0.65, 0.75, 0.85])
    ax[1, 0].set_xticks([5000, 10000, 15000])
    ax[1, 0].set_xticklabels([5000, 10000, 15000])

    ax[1, 1].set_ylim([0.64, 0.96])
    ax[1, 1].set_yticks([0.70, 0.8, 0.90])
    ax[1, 1].set_yticklabels([0.70, 0.8, 0.90])
    ax[1, 1].set_xticks([800, 1600, 2400])
    ax[1, 1].set_xticklabels([800, 1600, 2400])

    ax[1, 2].set_ylim([0.76, 1.01])
    ax[1, 2].set_yticks([0.82, 0.88, 0.94])
    ax[1, 2].set_yticklabels([0.81, 0.87, 0.93])
    ax[1, 2].set_xticks([2200, 4400, 6600])
    ax[1, 2].set_xticklabels([2200, 4400, 6600])
    plt.subplots_adjust(wspace=0.2, hspace=0.3)
    ax[0, 0].legend(loc='lower right', framealpha=1.0, frameon=None, borderpad=0.1,
                    labelspacing=0.2, handletextpad=0.1, markerfirst=True, fontsize=18)
    f_name = '--- config your path ---/' \
             'curves-all-imbalance-0-05-iter.pdf'
    fig.savefig(f_name, dpi=600, bbox_inches='tight', pad_inches=0, format='pdf')
    plt.close()


def show_all_parameter_select():
    import matplotlib.pyplot as plt
    from pylab import rcParams
    plt.rcParams['text.usetex'] = True
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.rcParams['text.latex.preamble'] = '\usepackage{libertine}'
    plt.rcParams["font.size"] = 20
    rcParams['figure.figsize'] = 12, 7
    list_methods = ['ftrl_auc', 'adagrad', 'rda_l1', 'ftrl_proximal']
    label_list = [r'FTRL-AUC', r'\textsc{AdaGrad}', r'RDA-$\displaystyle \ell^1$', r'\textsc{FTRL-Pro}']
    marker_list = ['s', 'D', 'o', '>', '>', '<', 'v', '^']
    color_list = ['r', 'b', 'g', 'm', 'y', 'c', 'm', 'black']
    fig, ax = plt.subplots(2, 3)
    for i, j in product(range(2), range(3)):
        ax[i, j].grid(color='gray', linewidth=0.5, linestyle='--', dashes=(10, 10))
        ax[i, j].spines['right'].set_visible(False)
        ax[i, j].spines['top'].set_visible(False)
    path = '--- config your path ---'
    data_fig5 = pkl.load(open(path + '/results/data_fig10.pkl'))
    title_list = ['(a) real-sim', '(b) farm-ads', '(c) rcv1b', '(d) imdb', '(e) reviews', '(f) news20b']
    for data_ind, dataset in enumerate(['03_real_sim', '08_farmads', '05_rcv1_bin',
                                        '10_imdb', '11_reviews', '02_news20b']):
        ii, jj = data_ind / 3, data_ind % 3
        for ind, method in enumerate(list_methods):
            xx, yy = data_fig5[dataset][(ii, jj)][method]
            ax[ii, jj].plot(xx, yy, marker=marker_list[ind], markersize=6.0, markerfacecolor='w',
                            markeredgewidth=1.5, linewidth=1.5, label=label_list[ind], color=color_list[ind])
            ax[ii, 0].set_ylabel('Sparse Ratio')
            ax[1, jj].set_xlabel('AUC')
            ax[ii, jj].set_yscale('log')
            ax[ii, jj].set_title(title_list[data_ind])
    for i in range(3):
        ax[0, i].set_ylim([0.0, 1.1])
        ax[0, i].set_yticks([0.0001, 0.001, 0.01, 0.1])
        ax[0, i].set_xlim([0.5, 1.0])
        ax[0, i].set_xticks([0.6, 0.7, 0.8, 0.9])
        ax[0, i].tick_params(labelbottom=False)
    ax[0, 0].set_yticks([0.0001, 0.001, 0.01, 0.1])
    ax[0, 1].tick_params(labelleft=False)
    ax[0, 2].tick_params(labelleft=False)
    ax[1, 0].set_yticks([0.0001, 0.001, 0.01, 0.1])
    ax[1, 1].tick_params(labelleft=False)
    ax[1, 2].tick_params(labelleft=False)

    for i, j in product(range(2), range(3)):
        ax[i, j].set_ylim([0.00001, 1.1])
        ax[i, j].set_yticks([0.0001, 0.001, 0.01, 0.1])
        ax[i, j].set_xlim([0.5, 1.0])
        ax[i, j].set_xticks([0.6, 0.7, 0.8, 0.9])

    plt.subplots_adjust(wspace=0.05, hspace=0.2)
    ax[0, 2].legend(fancybox=True, loc='lower right', framealpha=1.0, frameon=True, borderpad=0.1,
                    labelspacing=0.2, handletextpad=0.1, markerfirst=True, fontsize=18)
    f_name = '--- config your path ---/' \
             'para-select-all-imbalance-0-05.pdf'
    plt.savefig(f_name, dpi=600, bbox_inches='tight', pad_inches=0, format='pdf')
    plt.close()


def main():
    imbalance_ratio = 0.05
    if sys.argv[1] == 'run':
        run_high_dimensional(method=sys.argv[2],
                             dataset=sys.argv[3],
                             num_cpus=int(sys.argv[4]))
    elif sys.argv[1] == 'run_huge':
        run_huge_dimensional(method=sys.argv[2],
                             dataset=sys.argv[3],
                             task_id=int(sys.argv[4]))
    elif sys.argv[1] == 'show_auc':
        result_statistics(dataset=sys.argv[2], imbalance_ratio=imbalance_ratio)
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
    elif sys.argv[1] == 'show_all_auc':
        imbalance_ratio = 0.05
        all_matrix = []
        for dataset in ['08_farmads', '03_real_sim', '05_rcv1_bin',
                        '02_news20b', '11_reviews', '10_imdb']:
            aucs = []
            list_methods = ['ftrl_auc', 'adagrad', 'rda_l1', 'ftrl_proximal']
            for method in list_methods:
                results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_%.1f.pkl' %
                                        (dataset, dataset, method, imbalance_ratio)))
                te_auc = []
                for item in results:
                    metrics = item[-1]
                    te_auc.append(metrics[1])
                all_matrix.append(np.mean(np.asarray(te_auc)))
                a = ("%0.4f" % float(np.mean(np.asarray(te_auc)))).lstrip('0')
                b = ("%0.4f" % float(np.std(np.asarray(te_auc)))).lstrip('0')
                aucs.append('$\pm$'.join([a, b]))
            print('auc: '),
            print(' & '.join(aucs))
        all_matrix = np.reshape(np.asarray(all_matrix), newshape=(6, 4))
        for xx, yy in zip(np.mean(all_matrix, axis=0), np.std(all_matrix, axis=0)):
            print('%.4f$\pm$%.4f' % (xx, yy))
        for dataset in ['08_farmads', '03_real_sim', '05_rcv1_bin',
                        '02_news20b', '11_reviews', '10_imdb']:
            run_times = []
            for method in list_methods:
                results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_%.1f.pkl' %
                                        (dataset, dataset, method, imbalance_ratio)))
                run_time = []
                for item in results:
                    metrics = item[-1]
                    run_time.append(metrics[5])
                a = ("%0.3f" % float(np.mean(np.asarray(run_time))))
                b = ("%0.3f" % float(np.std(np.asarray(run_time))))
                run_times.append('$\pm$'.join([a, b]))
            print('run time:'),
            print(' & '.join(run_times))
        for dataset in ['08_farmads', '03_real_sim', '05_rcv1_bin',
                        '02_news20b', '11_reviews', '10_imdb']:
            sparse_ratios = []
            for method in list_methods:
                results = pkl.load(open(root_path + '%s/re_%s_%s_imbalance_%.1f.pkl' %
                                        (dataset, dataset, method, imbalance_ratio)))
                sparse_ratio = []
                for item in results:
                    metrics = item[-1]
                    sparse_ratio.append(metrics[3])
                a = ("%0.4f" % float(np.mean(np.asarray(sparse_ratio)))).lstrip('0')
                b = ("%0.4f" % float(np.std(np.asarray(sparse_ratio)))).lstrip('0')
                sparse_ratios.append('$\pm$'.join([a, b]))
            print('sparse-ratio: '),
            print(' & '.join(sparse_ratios))


if __name__ == '__main__':
    # get_data_fig10()
    # get_data_fig11()
    main()
