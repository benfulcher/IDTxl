"""Test IDTxl results class."""
import os
import pickle
import pytest
from tempfile import TemporaryFile
import itertools as it
import copy as cp
import numpy as np
from idtxl.multivariate_te import MultivariateTE
from idtxl.bivariate_te import BivariateTE
from idtxl.multivariate_mi import MultivariateMI
from idtxl.bivariate_mi import BivariateMI
from idtxl.network_comparison import NetworkComparison
from idtxl.data import Data
from idtxl.estimators_jidt import JidtDiscreteCMI
from test_estimators_jidt import jpype_missing

# Use common settings dict that can be used for each test
settings = {
    'cmi_estimator': 'JidtDiscreteCMI',
    'discretise_method': 'none',
    'alph1': 5,
    'alph2': 5,
    'alphc': 5,
    'n_perm_max_stat': 21,
    'n_perm_omnibus': 30,
    'n_perm_max_seq': 30,
    'min_lag_sources': 1,
    'max_lag_sources': 2,
    'max_lag_target': 1}


@jpype_missing
def test_results_network_inference():
    """Test results class for multivariate TE network inference."""
    covariance = 0.4
    n = 10000
    delay = 1
    normalisation = False
    source = np.random.normal(0, 1, size=n)
    target_1 = (covariance * source + (1 - covariance) *
                np.random.normal(0, 1, size=n))
    target_2 = (covariance * source + (1 - covariance) *
                np.random.normal(0, 1, size=n))
    expected_mi = np.log(1 / (1 - np.power(covariance, 2)))
    source = source[delay:]
    target_1 = target_1[:-delay]
    target_2 = target_2[:-delay]

    # Discretise data for speed
    settings_dis = {'discretise_method': 'equal',
                    'alph1': 5,
                    'alph2': 5}
    est = JidtDiscreteCMI(settings_dis)
    source_dis, target_1_dis = est._discretise_vars(var1=source, var2=target_1)
    source_dis, target_2_dis = est._discretise_vars(var1=source, var2=target_2)
    data = Data(np.vstack((source_dis, target_1_dis, target_2_dis)),
                dim_order='ps', normalise=normalisation)

    nw = MultivariateTE()
    # TE - single target
    res_single_multi_te = nw.analyse_single_target(
        settings=settings, data=data, target=1)
    # TE whole network
    res_network_multi_te = nw.analyse_network(settings=settings, data=data)

    nw = BivariateTE()
    # TE - single target
    res_single_biv_te = nw.analyse_single_target(
        settings=settings, data=data, target=1)
    # TE whole network
    res_network_biv_te = nw.analyse_network(settings=settings, data=data)

    nw = MultivariateMI()
    # TE - single target
    res_single_multi_mi = nw.analyse_single_target(
        settings=settings, data=data, target=1)
    # TE whole network
    res_network_multi_mi = nw.analyse_network(settings=settings, data=data)

    nw = BivariateMI()
    # TE - single target
    res_single_biv_mi = nw.analyse_single_target(
        settings=settings, data=data, target=1)
    # TE whole network
    res_network_biv_mi = nw.analyse_network(settings=settings, data=data)

    res_te = [res_single_multi_te, res_network_multi_te, res_single_biv_te,
               res_network_biv_te]
    res_mi = [res_single_multi_mi, res_network_multi_mi, res_single_biv_mi,
              res_network_biv_mi]
    res_all = res_te + res_mi

    # Check estimated values
    for res in res_te:
        est_te = res.single_target[1].omnibus_te
        assert np.isclose(est_te, expected_mi, atol=0.05), (
            'Estimated TE for discrete variables is not correct. Expected: '
            '{0}, Actual results: {1}.'.format(expected_mi, est_mi))
    for res in res_mi:
        est_mi = res.single_target[1].omnibus_mi
        assert np.isclose(est_mi, expected_mi, atol=0.05), (
            'Estimated TE for discrete variables is not correct. Expected: '
            '{0}, Actual results: {1}.'.format(expected_mi, est_mi))

    est_te = res_network_multi_te.single_target[2].omnibus_te
    assert np.isclose(est_te, expected_mi, atol=0.05), (
        'Estimated TE for discrete variables is not correct. Expected: {0}, '
        'Actual results: {1}.'.format(expected_mi, est_mi))
    est_mi = res_network_multi_mi.single_target[2].omnibus_mi
    assert np.isclose(est_mi, expected_mi, atol=0.05), (
        'Estimated TE for discrete variables is not correct. Expected: {0}, '
        'Actual results: {1}.'.format(expected_mi, est_mi))

    # Check data parameters in results objects
    n_nodes = 3
    n_realisations = n - delay - max(
        settings['max_lag_sources'], settings['max_lag_target'])
    for res in res_all:
        assert res.data.n_nodes == n_nodes, 'Incorrect no. nodes.'
        assert res.data.n_nodes == n_nodes, 'Incorrect no. nodes.'
        assert res.data.n_realisations == n_realisations, (
            'Incorrect no. realisations.')
        assert res.data.n_realisations == n_realisations, (
            'Incorrect no. realisations.')
        assert res.data.normalised == normalisation, (
            'Incorrect value for data normalisation.')
        assert res.data.normalised == normalisation, (
            'Incorrect value for data normalisation.')
        assert res.adjacency_matrix.shape[0] == n_nodes, (
            'Incorrect number of rows in adjacency matrix.')
        assert res.adjacency_matrix.shape[1] == n_nodes, (
            'Incorrect number of columns in adjacency matrix.')
        assert res.adjacency_matrix.shape[0] == n_nodes, (
            'Incorrect number of rows in adjacency matrix.')
        assert res.adjacency_matrix.shape[1] == n_nodes, (
            'Incorrect number of columns in adjacency matrix.')


def test_pickle_results():
    """Test pickling results objects."""
    data = _generate_gauss_data()
    nw = MultivariateTE()
    res_single = nw.analyse_single_target(
        settings=settings, data=data, target=1)
    res_network = nw.analyse_network(settings=settings, data=data)

    outfile = TemporaryFile()
    pickle.dump(res_single, outfile)
    pickle.dump(res_network, outfile)


def test_combine_results():
    """Test combination of results objects."""
    data = _generate_gauss_data()
    nw = MultivariateTE()
    res_network_1 = nw.analyse_network(settings=settings, data=data)

    # Test error for unequal settings
    res_network_2 = cp.deepcopy(res_network_1)
    res_network_2.settings.add_conditionals = 'Test'
    with pytest.raises(RuntimeError):
        res_network_1.combine_results(res_network_2)


def test_add_single_result():
    """Test adding results for a single target/process."""
    data = _generate_gauss_data()
    nw = MultivariateTE()
    res_network = nw.analyse_single_target(
        settings=settings, data=data, target=1)

    # Test adding target results that already exists
    with pytest.raises(RuntimeError):
        res_network._add_single_result(target=1,
                                       settings=res_network.settings,
                                       results={})
    # Test adding target results with unequal settings
    settings_test = cp.deepcopy(res_network.settings)
    settings_test.add_conditionals = 'Test'
    with pytest.raises(RuntimeError):
        res_network._add_single_result(target=0,
                                       settings=settings_test,
                                       results=res_network.single_target[1])
    # Test adding a target with additional settings, results.settings should be
    # updated
    settings_test = cp.deepcopy(res_network.settings)
    settings_test.new_setting = 'Test'
    res_network._add_single_result(target=0,
                                   settings=settings_test,
                                   results=res_network.single_target[1])
    assert 'new_setting' in res_network.settings.keys(), (
        'Settings dict was not updated.')
    assert res_network.settings.new_setting == 'Test', (
        'Settings dict was not updated correctly.')


def test_delay_reconstruction():
    """Test the reconstruction of information transfer delays from results."""
    covariance = 0.4
    expected_mi = np.log(1 / (1 - np.power(covariance, 2)))
    n = 10000
    delay_1 = 1
    delay_2 = 3
    delay_3 = 5
    normalisation = False
    source = np.random.normal(0, 1, size=n)
    target_1 = (covariance * source + (1 - covariance) *
                np.random.normal(0, 1, size=n))
    target_2 = (covariance * source + (1 - covariance) *
                np.random.normal(0, 1, size=n))
    target_3 = (covariance * source + (1 - covariance) *
                np.random.normal(0, 1, size=n))
    source = source[delay_3:]
    target_1 = target_1[(delay_3-delay_1):-delay_1]
    target_2 = target_2[(delay_3-delay_2):-delay_2]
    target_3 = target_3[:-delay_3]

    # Discretise data for speed
    settings_dis = {'discretise_method': 'equal',
                    'alph1': 5,
                    'alph2': 5}
    est = JidtDiscreteCMI(settings_dis)
    source_dis, target_1_dis = est._discretise_vars(var1=source, var2=target_1)
    source_dis, target_2_dis = est._discretise_vars(var1=source, var2=target_2)
    source_dis, target_3_dis = est._discretise_vars(var1=source, var2=target_3)
    data = Data(
        np.vstack((source_dis, target_1_dis, target_2_dis, target_3_dis)),
        dim_order='ps', normalise=normalisation)

    nw = MultivariateTE()
    settings = {
        'cmi_estimator': 'JidtDiscreteCMI',
        'discretise_method': 'none',
        'alph1': 5,
        'alph2': 5,
        'alphc': 5,
        'n_perm_max_stat': 21,
        'n_perm_omnibus': 30,
        'n_perm_max_seq': 30,
        'min_lag_sources': 1,
        'max_lag_sources': delay_3 + 1,
        'max_lag_target': 1}

    res_network = nw.analyse_single_target(
        settings=settings, data=data, target=1)
    res_network.combine_results(nw.analyse_single_target(
        settings=settings, data=data, target=2))
    res_network.combine_results(nw.analyse_single_target(
        settings=settings, data=data, target=3))
    print(res_network.adjacency_matrix)
    assert res_network.adjacency_matrix[0, 1] == delay_1, (
        'Delay 1 was not reconstructed correctly.')
    assert res_network.adjacency_matrix[0, 2] == delay_2, (
        'Delay 2 was not reconstructed correctly.')
    assert res_network.adjacency_matrix[0, 3] == delay_3, (
        'Delay 3 was not reconstructed correctly.')

    for target in range(1, 4):
        est_mi = res_network.single_target[target].omnibus_te
        assert np.isclose(est_mi, expected_mi, atol=0.05), (
            'Estimated TE for target {0} is not correct. Expected: {1}, '
            'Actual results: {2}.'.format(target, expected_mi, est_mi))


def _generate_gauss_data(covariance=0.4, n=10000, delay=1, normalise=False):
    # Generate two coupled Gaussian time series
    source = np.random.normal(0, 1, size=n)
    target = (covariance * source + (1 - covariance) *
              np.random.normal(0, 1, size=n))
    source = source[delay:]
    target = target[:-delay]

    # Discretise data for speed
    settings = {'discretise_method': 'equal',
                'alph1': 5,
                'alph2': 5}
    est = JidtDiscreteCMI(settings)
    source_dis, target_dis = est._discretise_vars(var1=source, var2=target)
    return Data(np.vstack((source_dis, target_dis)),
                dim_order='ps', normalise=normalise)


def test_console_output():
    data = Data()
    data.generate_mute_data(n_samples=10, n_replications=5)
    settings = {
        'cmi_estimator': 'JidtKraskovCMI',
        'max_lag_sources': 5,
        'min_lag_sources': 4,
        'max_lag_target': 5
        }
    nw = MultivariateTE()
    r = nw.analyse_network(settings, data, targets='all', sources='all')
    r.print_to_console(fdr=False)


def test_results_network_comparison():
    """Test results class for network comparison."""
    data_0 = Data()
    data_0.generate_mute_data(500, 5)
    data_1 = Data(np.random.rand(5, 500, 5), 'psr')

    path = os.path.join(os.path.dirname(__file__), 'data/')
    res_0 = pickle.load(open(path + 'mute_results_0.p', 'rb'))
    res_1 = pickle.load(open(path + 'mute_results_1.p', 'rb'))

    # comparison settings
    comp_settings = {
            'cmi_estimator': 'JidtKraskovCMI',
            'n_perm_max_stat': 50,
            'n_perm_min_stat': 50,
            'n_perm_omnibus': 200,
            'n_perm_max_seq': 50,
            'alpha_comp': 0.26,
            'n_perm_comp': 200,
            'tail': 'two',
            'permute_in_time': True,
            'perm_type': 'random'
            }
    comp = NetworkComparison()

    comp_settings['stats_type'] = 'independent'
    res_within = comp.compare_within(
        comp_settings, res_0, res_1, data_0, data_1)
    comp_settings['stats_type'] = 'independent'
    res_between = comp.compare_between(
        comp_settings,
        network_set_a=np.array(list(it.repeat(res_0, 10))),
        network_set_b=np.array(list(it.repeat(res_1, 10))),
        data_set_a=np.array(list(it.repeat(data_0, 10))),
        data_set_b=np.array(list(it.repeat(data_1, 10))))
    s = 0
    t = [1, 2]
    test = ['Within', 'Between']
    for (i, res) in enumerate([res_within, res_between]):
        # Union network
        # TODO do we need the max_lag entry?
        assert (res.adjacency_matrix_union[s, t] == 1).all(), (
            '{0}-test did not return correct union network links.'.format(
                test[i]))
        no_diff = np.extract(np.invert(res.adjacency_matrix_comparison),
                             res.adjacency_matrix_union)
        assert (no_diff == 0).all(), (
            '{0}-test did not return 0 in union network for no links.'.format(
                test[i]))
        # Comparison
        assert res.adjacency_matrix_comparison[s, t].all(), (
            '{0}-test did not return correct comparison results.'.format(
                test[i]))
        no_diff = np.extract(np.invert(res.adjacency_matrix_comparison),
                             res.adjacency_matrix_comparison)
        assert (no_diff == 0).all(), (
            '{0}-test did not return 0 comparison for non-sign. links.'.format(
                test[i]))
        # Abs. difference
        assert (res.adjacency_matrix_diff_abs[s, t] > 0).all(), (
            '{0}-test did not return correct absolute differences.'.format(
                test[i]))
        no_diff = np.extract(np.invert(res.adjacency_matrix_comparison),
                             res.adjacency_matrix_diff_abs)
        assert (no_diff == 0).all(), (
            '{0}-test did not return 0 difference for non-sign. links.'.format(
                test[i]))
        # p-value
        p_max = 1 / comp_settings['n_perm_comp']
        assert (res.adjacency_matrix_pvalue[s, t] == p_max).all(), (
            '{0}-test did not return correct p-value for sign. links.'.format(
                test[i]))
        no_diff = np.extract(np.invert(res.adjacency_matrix_comparison),
                             res.adjacency_matrix_pvalue)
        assert (no_diff == 1).all(), (
            '{0}-test did not return p-vals of 1 for non-sign. links.'.format(
                test[i]))

def test_export_brain_net():
    """Test export to BrainNet Viewer toolbox."""
    n_nodes = 5
    data_0 = Data()
    data_0.generate_mute_data(500, 5)
    data_1 = Data(np.random.rand(n_nodes, 500, 5), 'psr')

    path = os.path.join(os.path.dirname(__file__), 'data/')
    res_0 = pickle.load(open(path + 'mute_results_0.p', 'rb'))
    res_1 = pickle.load(open(path + 'mute_results_1.p', 'rb'))

    outfile = '{0}brain_net'.format(path)
    # Export of network inference results.
    mni_coord = np.random.randint(10, size=(n_nodes, 3))
    node_color = np.random.randint(10, size=n_nodes)
    node_size = np.random.randint(10, size=n_nodes)
    labels = ['node_0', 'node_1', 'node_2', 'node_3', 'node_4']
    res_0.export_brain_net_viewer(mni_coord=mni_coord,
                                  file_name=outfile,
                                  labels=labels,
                                  node_color=node_color,
                                  node_size=node_size)

    # Export of network comparison results.
    comp_settings = {
            'cmi_estimator': 'JidtKraskovCMI',
            'stats_type': 'independent',
            'n_perm_max_stat': 50,
            'n_perm_min_stat': 50,
            'n_perm_omnibus': 200,
            'n_perm_max_seq': 50,
            'alpha_comp': 0.26,
            'n_perm_comp': 200,
            'tail': 'two',
            'permute_in_time': True,
            'perm_type': 'random'
            }
    comp = NetworkComparison()
    res_within = comp.compare_within(
        comp_settings, res_0, res_1, data_0, data_1)
    for matrix in ['union', 'comparison', 'pvalue', 'diff_abs']:
        res_within.export_brain_net_viewer(matrix=matrix,
                                           mni_coord=mni_coord,
                                           file_name=outfile,
                                           labels=labels,
                                           node_color=node_color,
                                           node_size=node_size)

    # Test checks for input.
    with pytest.raises(AssertionError):
        res_within._export_brain_net(adjacency_matrix=np.ones((3, 10)),
                                     mni_coord=mni_coord[:3, :],
                                     file_name=outfile)
    with pytest.raises(AssertionError):
        res_within.export_brain_net_viewer(matrix=matrix,
                                           mni_coord=mni_coord[:3, :],
                                           file_name=outfile)
    with pytest.raises(AssertionError):
        res_within.export_brain_net_viewer(matrix=matrix,
                                           mni_coord=mni_coord[:, :2],
                                           file_name=outfile)
    with pytest.raises(AssertionError):
        res_within.export_brain_net_viewer(matrix=matrix,
                                           mni_coord=mni_coord,
                                           file_name=outfile,
                                           labels=['node_1', 'node_2'])
    with pytest.raises(AssertionError):
        res_within.export_brain_net_viewer(matrix=matrix,
                                           mni_coord=mni_coord,
                                           file_name=outfile,
                                           node_color=np.arange(n_nodes + 1))
    with pytest.raises(AssertionError):
        res_within.export_brain_net_viewer(matrix=matrix,
                                           mni_coord=mni_coord,
                                           file_name=outfile,
                                           node_color=np.arange(n_nodes + 1))


if __name__ == '__main__':
    test_export_brain_net()
    test_results_network_inference()
    test_results_network_comparison()
    test_console_output()
    test_pickle_results()
    test_delay_reconstruction()
    test_combine_results()
    test_add_single_result()
