import tensorflow as tf

# Hyper-parameters.
flags = tf.app.flags

# flags.DEFINE_string('special_note', 'fix results.py', 'Special note.')

# For data preprocessing.
""" dataset: aids80nef, aids700nef, linux, imdbmulti, alkane, nasa, nci109, 
             aids700nef, ptc, reddit10k, collab, mutag, linux_imdb. """
dataset = 'aids700nef'
dataset_train = dataset
dataset_val_test = dataset
dataset_super_large = False
if 'aids' in dataset or dataset in ['alkane', 'webeasy', 'nci109', 'ptc', 'mutag']:
    node_feat_name = 'type'
    node_feat_encoder = 'onehot'
    max_nodes = 10
    num_glabels = 2
    if dataset == 'webeasy':
        max_nodes = 404
        num_glabels = 20
    if dataset == 'nci109':
        max_nodes = 106
    if dataset == 'ptc':
        max_nodes = 109
    if dataset == 'mutag':
        max_nodes = 28
    if dataset == 'aids80nef':
        num_glabels = 10
        # dataset_super_large = True
elif dataset in ['linux', 'nasa', 'reddit10k', 'collab'] or 'imdb' in dataset:
    node_feat_name = None
    node_feat_encoder = 'constant_1'
    if dataset == 'linux' or dataset == 'nasa':
        max_nodes = 10
        num_glabels = 2
    elif dataset == 'reddit10k':
        max_nodes = 3782
        num_glabels = 11
        dataset_val_test = 'reddit10ksmall'
        # dataset_super_large = True
    elif dataset == 'collab':
        max_nodes = 492
        num_glabels = 3
        dataset_super_large = True
    else:
        assert ('imdb' in dataset)
        max_nodes = 90
        num_glabels = 3
else:
    assert (False)
if 'imdbmulti' in [dataset_train, dataset_val_test]:
    max_nodes = 90
flags.DEFINE_string('dataset_train', dataset_train, 'Dataset for training.')
flags.DEFINE_string('dataset_val_test', dataset_val_test, 'Dataset for testing.')
flags.DEFINE_boolean('dataset_super_large', dataset_super_large,
                     'Whether one of the two datasets is super large.')
flags.DEFINE_integer('num_glabels', num_glabels, 'Number of graph labels in the dataset.')
flags.DEFINE_string('node_feat_name', node_feat_name, 'Name of the node feature.')
flags.DEFINE_string('node_feat_encoder', node_feat_encoder,
                    'How to encode the node feature.')
""" valid_percentage: (0, 1). """
flags.DEFINE_float('valid_percentage', 0.25,
                   '(# validation graphs) / (# validation + # training graphs.')
""" ds_metric: ged, glet, mcs. """
ds_metric = 'ged'
flags.DEFINE_string('ds_metric', ds_metric, 'Distance/Similarity metric to use.')
""" ds_algo: beam80, astar for ged, graphlet for glet, mccreesh2017 for mcs. """
ds_algo = 'astar' if ds_metric == 'ged' else 'mccreesh2017'
flags.DEFINE_string('ds_algo', ds_algo,
                    'Ground-truth distance algorithm to use.')
""" ordering: 'bfs', 'degree', None. """
flags.DEFINE_string('ordering', 'bfs', '')
""" coarsening: 'metis_<num_level>', None. """
flags.DEFINE_string('coarsening', None, 'Algorithm for graph coarsening.')

# For model.
""" model: 'siamese_regression', 'siamese_regression_transductive',
           'siamese_regression', 'siamese_classification', 'siamese_matching'. """
model = 'siamese_regression'  # model is here!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
flags.DEFINE_string('model', model, 'Model string.')
""" model_name: 'SimGNN', 'GSimCNN', None. """
flags.DEFINE_string('model_name', 'Our Model', 'Model name string.')
flags.DEFINE_integer('batch_size', 128, 'Number of graph pairs in a batch.')
flags.DEFINE_boolean('ds_norm', True,
                     'Whether to normalize the distance or not '
                     'when choosing the ground truth distance.')
flags.DEFINE_boolean('node_embs_norm', True,
                     'Whether to normalize the node embeddings or not.')
need_gc = False
pred_sim_dist, supply_sim_dist = None, None
if model in ['siamese_regression', 'siamese_regression_transductive', 'siamese_matching']:
    """ ds_kernel: gaussian, exp, inverse, identity. """
    ds_kernel = 'exp'
    if ds_metric == 'glet':  # already a sim metric
        ds_kernel = 'identity'
    flags.DEFINE_string('ds_kernel', ds_kernel,
                        'Name of the similarity kernel.')
    if ds_kernel == 'gaussian':
        """ yeta:
         if ds_norm, try 0.6 for nef small, 0.3 for nef, 0.2 for regular;
         else, try 0.01 for nef, 0.001 for regular. """
        flags.DEFINE_float('yeta', 0.01, 'yeta for the gaussian kernel function.')
    elif ds_kernel == 'exp' or ds_kernel == 'inverse':
        flags.DEFINE_float('scale', 0.7, 'Scale for the exp/inverse kernel function.')
    pred_sim_dist = 'sim' # check!!!!!!!!!!!!!!!!!!!!!!!!!
    if ds_metric == 'mcs':
        pred_sim_dist = 'sim'  # cannot support it for now
    supply_sim_dist = pred_sim_dist
    # Start of mse loss.
    lambda_msel = 1  # 1  # 1 #0.0001
    if lambda_msel > 0:
        flags.DEFINE_float('lambda_mse_loss', lambda_msel,
                           'Lambda for the mse loss.')
    # End of mse loss.
    # Start of weighted distance loss.
    lambda_wdl = 0  # 1#1  # 1
    if lambda_wdl > 0:
        flags.DEFINE_float('lambda_weighted_dist_loss', lambda_wdl,
                           'Lambda for the weighted distance loss.')
        supply_sim_dist = 'sim'  # special for wdl loss
        # flags.DEFINE_boolean('graph_embs_norm', True,
        #                      'Whether to normalize the graph embeddings or not.')
    # End of weighted distance loss.
    # Start of trivial solution avoidance loss.
    lambda_tsl = 0
    if lambda_tsl > 0:
        flags.DEFINE_float('lambda_triv_avoid_loss', lambda_tsl,
                           'Lambda for the trivial solution avoidance loss.')
    # End of trivial solution avoidance loss.
    # Start of diversity encouraging loss.
    lambda_del = 0
    if lambda_del > 0:
        flags.DEFINE_float('lambda_diversity_loss', lambda_del,
                           'Lambda for the diversity encouraging loss.')
    # End of diversity encouraging loss.
    # Start of graph classification loss.
    lambda_gcl = 0
    if lambda_gcl > 0:
        need_gc = True
        flags.DEFINE_float('lambda_gc_loss', lambda_gcl,
                           'Lambda for the softmax cross entropy '
                           'graph classification loss.')
        # End of graph classification loss.
elif model == 'siamese_ranking':
    pred_sim_dist = 'sim'
    supply_sim_dist = 'dist'
    # # Start of hinge loss.
    """ delta and gamma: depend on whether ds_norm is True of False. """
    flags.DEFINE_float('delta', 0.6,
                       'Margin between positive pairs ground truth scores'
                       'and negative pairs scores ground truth scores')
    flags.DEFINE_float('gamma', 0.6,
                       'Margin between positive pairs prediction scores'
                       'and negative pairs prediction scores')
    flags.DEFINE_integer('num_neg', 8, 'Number of negative samples.')
    flags.DEFINE_integer('top_k', 0, 'Sample positive & negative pairs from top k samples after sort.')
    # flags.DEFINE_float('pos_thresh', 0.35, 'sample positive & negative pairs from top n samples after sort')
    # End of hinge loss.
flags.DEFINE_string('pred_sim_dist', pred_sim_dist,
                    'dist/sim indicating whether the model is predicting dist or sim.')
flags.DEFINE_string('supply_sim_dist', supply_sim_dist,
                    'dist/sim indicating whether the model should supply dist or sim.')
layer = 0
layer += 1
if model in ['siamese_regression', 'siamese_ranking', 'siamese_matching']:
    '''
    # # --------------------------------- MNE+CNN ---------------------------------
    layer = 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'GraphConvolution:output_dim=128,dropout=False,bias=True,'
        'act=relu,sparse_inputs=True', '')
    layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Coarsening:pool_style=avg', '')
    # layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'GraphConvolution:input_dim=128,output_dim=64,dropout=False,bias=True,'
        'act=relu,sparse_inputs=False', '')
    layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Coarsening:pool_style=avg', '')
    # layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'GraphConvolution:input_dim=64,output_dim=32,dropout=False,bias=True,'
        'act=identity,sparse_inputs=False', '')
    layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Coarsening:pool_style=avg', '')
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'GraphConvolution:input_dim=32,output_dim=32,dropout=False,bias=True,'
    #     'act=identity,sparse_inputs=False', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'GraphConvolution:input_dim=32,output_dim=32,dropout=False,bias=True,'
    #     'act=identity,sparse_inputs=False', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_6',
    #     'GraphConvolution:input_dim=32,output_dim=32,dropout=False,bias=True,'
    #     'act=relu,sparse_inputs=False', '')
    # flags.DEFINE_string(
    #     'layer_7',
    #     'GraphConvolution:input_dim=32,output_dim=32,dropout=False,bias=True,'
    #     'act=identity,sparse_inputs=False', '')
    # flags.DEFINE_string(
    #     'layer_4',
    #     'GraphConvolution:input_dim=32,output_dim=32,dropout=False,bias=True,'
    #     'act=identity,sparse_inputs=False', '')
    #  *************************** GraphConvolutionCollector Layer ***************************
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Average', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Dot:output_dim=1,act=identity', '')
    gcn_num = 3
    mode = 'separate'  # merge, separate (better)
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'GraphConvolutionCollector:gcn_num={},'
        'fix_size=54,mode=0,padding_value=0,align_corners=True'.format(gcn_num), '')
    layer += 1
    # --------------------------- MNEResize Layer ---------------------------
    # Fix_Size: 90 imdbmulti, 10 others
    # Mode: 0 Bilinear interpolation, 1 Nearest neighbor interpolation,
    #       2 Bicubic interpolation, 3 Area interpolation
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'MNEResize:fix_size=10,mode=0,dropout=False,inneract=identity,'
    #     'padding_value=0,align_corners=True', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'PadandTruncate:padding_value=0', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'MNE:input_dim=32,dropout=False,inneract=identity', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'CNN:start_cnn=True,end_cnn=False,window_size=200,kernel_stride=1,'
    #     'in_channel=1,out_channel=16,'
    #     'padding=SAME,pool_size=3,dropout=False,act=relu,bias=True,'
    #     'mode={},gcn_num={}'.format(mode, gcn_num), '')
    # layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'CNN:start_cnn=True,end_cnn=False,window_size=25,kernel_stride=1,'
        'in_channel=1,out_channel=16,'
        'padding=SAME,pool_size=3,dropout=False,act=relu,bias=True,'
        'mode={},gcn_num={}'.format(mode, gcn_num), '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'CNN:start_cnn=False,end_cnn=False,window_size=10,kernel_stride=1,'
        'in_channel=16,out_channel=32,'
        'padding=SAME,pool_size=3,dropout=False,act=relu,bias=True,'
        'mode={},gcn_num={}'.format(mode, gcn_num), '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'CNN:start_cnn=False,end_cnn=False,window_size=4,kernel_stride=1,'
        'in_channel=32,out_channel=64,'
        'padding=SAME,pool_size=3,dropout=False,act=relu,bias=True,'
        'mode={},gcn_num={}'.format(mode, gcn_num), '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'CNN:start_cnn=False,end_cnn=True,window_size=2,kernel_stride=1,'
        'in_channel=64,out_channel=128,'
        'padding=SAME,pool_size=2,dropout=False,act=relu,bias=True,'
        'mode={},gcn_num={}'.format(mode, gcn_num), '')
    layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'CNN:start_cnn=False,end_cnn=False,window_size=5,kernel_stride=1,'
    #     'in_channel=128,out_channel=128,'
    #     'padding=SAME,pool_size=3,dropout=False,act=relu,bias=True,'
    #     'mode={},gcn_num={}'.format(mode, gcn_num), '')
    # layer += 1
    # #
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'CNN:start_cnn=False,end_cnn=False,window_size=5,kernel_stride=1,'
    #     'in_channel=128,out_channel=128,'
    #     'padding=SAME,pool_size=3,dropout=False,act=relu,bias=True,'
    #     'mode={},gcn_num={}'.format(mode, gcn_num), '')
    # layer += 1
    #
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'CNN:start_cnn=False,end_cnn=False,window_size=5,kernel_stride=1,'
    #     'in_channel=128,out_channel=128,'
    #     'padding=SAME,pool_size=3,dropout=False,act=relu,bias=True,'
    #     'mode={},gcn_num={}'.format(mode, gcn_num), '')
    # layer += 1
    # #
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'CNN:start_cnn=False,end_cnn=True,window_size=5,kernel_stride=1,'
    #     'in_channel=128,out_channel=128,'
    #     'padding=SAME,pool_size=3,dropout=False,act=relu,bias=True,'
    #     'mode={},gcn_num={}'.format(mode, gcn_num), '')
    # layer += 1

    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'CNN:start_cnn=False,end_cnn=True,window_size=5,kernel_stride=1,'
    #     'in_channel=128,out_channel=128,'
    #     'padding=SAME,pool_size=3,dropout=False,act=relu,bias=True,'
    #     'mode={},gcn_num={}'.format(mode, gcn_num), '')
    # layer += 1
    #
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'CNN:start_cnn=False,end_cnn=True,window_size=5,kernel_stride=1,in_channel=128,out_channel=128,'
    #     'padding=SAME,pool_size=3,dropout=False,act=relu,bias=True,mode=separate,gcn_num=3', '')
    # layer += 1

    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Dense:input_dim=640,output_dim=512,dropout=False,'
    #     'act=relu,bias=True', '')
    # layer += 1

    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=384,output_dim=256,dropout=False,'
        'act=relu,bias=True', '')
    layer += 1

    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=256,output_dim=128,dropout=False,'
        'act=relu,bias=True', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=128,output_dim=64,dropout=False,'
        'act=relu,bias=True', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=64,output_dim=32,dropout=False,'
        'act=relu,bias=True', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=32,output_dim=16,dropout=False,'
        'act=relu,bias=True', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=16,output_dim=8,dropout=False,'
        'act=relu,bias=True', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=8,output_dim=4,dropout=False,'
        'act=relu,bias=True', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=4,output_dim=1,dropout=False,'
        'act=identity,bias=True', '')
    flags.DEFINE_integer('layer_num', layer, 'Number of layers.')

    # --------------------------------- Branch. ---------------------------------

    flags.DEFINE_integer('branch_from', 4, 'Branch layer index (1-based).')
    layer = 0
    # layer += 1 # TODO: later use Transformer architecture
    # flags.DEFINE_string(
    #     'branch_layer_{}'.format(layer),
    #     'Dense:input_dim=4,output_dim=1,dropout=False,'
    #     'act=identity,bias=True', '')
    flags.DEFINE_integer('branch_layer_num', layer, 'Number of layers in the branch.')
    # Start of matching loss.
    lambda_mne_loss = 1  # 1  # 1 #0.0001
    if lambda_mne_loss > 0:
        flags.DEFINE_float('lambda_mne_loss', lambda_mne_loss,
                           'Lambda for the mne (node matching) loss.')
        flags.DEFINE_string('pred_mne_mat_from', 'layer_4', # branch_layer_5
                           'Layer whose output is the MNE matrix.')
    # End of matching loss.


    '''

    #'''
    # --------------------------------- ATT+NTN ---------------------------------
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'GraphConvolution:output_dim=64,dropout=False,bias=True,'
        'act=relu,sparse_inputs=True', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Coarsening:pool_style=avg', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'GraphConvolution:input_dim=64,output_dim=32,dropout=False,bias=True,'
        'act=relu,sparse_inputs=False', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Coarsening:pool_style=avg', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'GraphConvolution:input_dim=32,output_dim=16,dropout=False,bias=True,'
        'act=identity,sparse_inputs=False', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Coarsening:pool_style=avg', '')
    # layer += 1
    # flags.DEFINE_string(
    #    'layer_{}'.format(layer),
    #    'Average', '') # Supersource, Average
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Attention:input_dim=32,att_times=1,att_num=1,att_weight=True,att_style=dot', '')
    # gcn_num = 3
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'JumpingKnowledge:gcn_num={},'
    #     'input_dims=256_128_64,att_times=1,att_num=1,att_weight=True,att_style=dot,'
    #     'combine_method=concat'.format(gcn_num), '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'NTN:input_dim=64,feature_map_dim=64,dropout=False,bias=True,'
    #     'inneract=relu,apply_u=False', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'ANPM:input_dim=16,att_times=1,att_num=1,att_style=dot,att_weight=True,'
        'feature_map_dim=16,dropout=False,bias=True,'
        'ntn_inneract=relu,apply_u=False,'
        'padding_value=0,'
        'mne_inneract=identity,mne_method=hist_16,branch_style=anpm', '')
    # flags.DEFINE_string(
    #     'layer_4',
    #     'ANPMD:input_dim=16,att_times=1,att_num=1,att_style=dot,att_weight=True,'
    #     'feature_map_dim=16,dropout=False,bias=True,'
    #     'ntn_inneract=relu,apply_u=False,'
    #     'padding_value=0,'
    #     'mne_inneract=sigmoid,mne_method=hist_16,branch_style=anpm,'
    #     'dense1_dropout=False,dense1_act=relu,dense1_bias=True,dense1_output_dim=8,'
    #     'dense2_dropout=False,dense2_act=relu,dense2_bias=True,dense2_output_dim=4', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=32,output_dim=16,dropout=False,bias=True,'
        'act=relu', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=16,output_dim=8,dropout=False,bias=True,'
        'act=relu', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=8,output_dim=4,dropout=False,bias=True,'
        'act=relu', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Dense:input_dim=8,output_dim=4,dropout=False,bias=True,'
    #     'act=relu', '')
    layer += 1
    flags.DEFINE_string(
        'layer_{}'.format(layer),
        'Dense:input_dim=4,output_dim=1,dropout=False,bias=True,'
        'act=identity', '')

    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Dense:input_dim=1,output_dim=1,dropout=False,bias=True,'
    #     'act=relu', '')

    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Dense:input_dim=448,output_dim=348,dropout=False,bias=True,'
    #     'act=relu', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Dense:input_dim=348,output_dim=256,dropout=False,bias=True,'
    #     'act=relu', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Dense:input_dim=64,output_dim=128,dropout=False,bias=True,'
    #     'act=relu', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Dense:input_dim=128,output_dim=256,dropout=False,bias=True,'
    #     'act=relu', '')
    # layer += 1
    # flags.DEFINE_string(
    #     'layer_{}'.format(layer),
    #     'Dense:input_dim=256,output_dim=256,dropout=False,bias=True,'
    #     'act=identity', '')
    # flags.DEFINE_integer('gemb_layer_id', layer, 'Layer index (1-based) '
    #                                              'to obtain graph embeddings.')
#     layer += 1
# if 'transductive' in model:
#     flags.DEFINE_integer('gemb_dim', 16,
#                          'Dimension of graph-level embeddings.')
# if model in ['siamese_regression', 'siamese_regression_transductive',
#              'siamese_ranking']:
#     if flags.FLAGS.pred_sim_dist == 'dist':
#         flags.DEFINE_string(
#             'layer_{}'.format(layer), 'Dist:norm=None', '')
#     else:
#         flags.DEFINE_string(
#             'layer_{}'.format(layer), 'Dot:output_dim=1,act=identity', '')
#     if need_gc:
#         # Gradually reduce graph embedding dim until reaching final label dim.
#         gembed_dim = 256
#         inter_dim1 = int(gembed_dim * (2 / 3) + num_glabels * (1 / 3))
#         inter_dim2 = int(gembed_dim * (1 / 3) + num_glabels * (2 / 3))
#         inter_dim3 = int(gembed_dim * 0 + num_glabels * 4)
#         flags.DEFINE_string(
#             'gc_layer_1'.format(layer),
#             'Dense:input_dim={},output_dim={},dropout=False,bias=True,'
#             'act=relu'.format(gembed_dim, inter_dim1), '')
#         flags.DEFINE_string(
#             'gc_layer_2'.format(layer),
#             'Dense:input_dim={},output_dim={},dropout=False,bias=True,'
#             'act=relu'.format(inter_dim1, inter_dim2), '')
#         flags.DEFINE_string(
#             'gc_layer_3'.format(layer),
#             'Dense:input_dim={},output_dim={},dropout=False,bias=True,'
#             'act=relu'.format(inter_dim2, inter_dim3), '')
#         flags.DEFINE_string(
#             'gc_layer_4'.format(layer),
#             'Dense:input_dim={},output_dim={},dropout=False,bias=True,'
#             'act=identity'.format(inter_dim3, num_glabels), '')
#         flags.DEFINE_integer('gc_layer_num', 4, 'Number of gc layers.')
#         flags.DEFINE_integer('layer_num', layer, 'Number of layers.')
    #'''
    flags.DEFINE_integer('layer_num', layer, 'Number of layers.')
if model == 'siamese_classification':
    pass

    flags.DEFINE_integer('layer_num', 0, 'Number of layers.')

    # Start of cross entropy loss.
    """
    aids700nef:    0.65 0.74 0.83 0.89 0.95 1.0  1.2  1.25 1.49
    linux:         0.25 0.35 0.43 0.53 0.58 0.67 0.78 0.89 1.1
    imdb1kcoarse:  0.45 0.6  0.77 0.88 0.99 1.15 1.35 1.65 2.1
    """
    if 'aids' in dataset:
        thresh = 0.95
        # thresh = 0.65
    elif dataset == 'linux':
        thresh = 0
        # thresh = 0.25
    elif 'imdb' in dataset:
        thresh = 0.99
        # thresh = 0.45
    else:
        assert (False)
    assert (flags.FLAGS.ds_norm)
    flags.DEFINE_float('thresh_train_pos', thresh,
                       'Threshold below which train pairs are similar.')
    flags.DEFINE_float('thresh_train_neg', thresh,
                       'Threshold above which train pairs are dissimilar.')
    flags.DEFINE_float('thresh_val_test_pos', thresh,
                       'Threshold that binarizes test pairs.')
    flags.DEFINE_float('thresh_val_test_neg', thresh,
                       'Threshold that binarizes test pairs.')
    # End of cross entropy loss.

# Start of graph loss.
""" graph_loss: '1st', None. """
graph_loss = None
flags.DEFINE_string('graph_loss', graph_loss, 'Loss function(s) to use.')
if graph_loss:
    flags.DEFINE_float('graph_loss_alpha', 0.,
                       'Weight parameter for the graph loss function.')
# End of graph loss.

# Generater and permutater.
fake_from, fake_gen = None, None
# fake_from, fake_gen = 'all_traings', '2_sp'
# if dataset_super_large:
#     fake_from = '10_traings'  # for __ train gs
#     fake_gen = '10_isotop_10%'  # generate __ isotop graphs (iso, 10%, 10%)
flags.DEFINE_string('train_fake_from', fake_from, '')
flags.DEFINE_string('train_fake_gen', fake_gen, '')
flags.DEFINE_float('train_real_percent', 1, '')

# Supersource node.
# Referenced as "super node" in https://arxiv.org/pdf/1511.05493.pdf.
# Node that is connected to all other nodes in the graph.
flags.DEFINE_boolean('supersource', False,
                     'Boolean. Whether or not to use a supersouce node in all of the graphs.')
# Random walk generation and usage.
# As used in the GraphSAGE model implementation: https://github.com/williamleif/GraphSAGE.
flags.DEFINE_string('random_walk', None,
                    'Random walk configuration. Set none to not use random walks. Format is: '
                    '<num_walks>_<walk_length>')

# Training (optimiztion) details.
flags.DEFINE_float('dropout', 0, 'Dropout rate (1 - keep probability).')
flags.DEFINE_float('weight_decay', 0,
                   'Weight for L2 loss on embedding matrix.')
""" learning_rate: 0.01 recommended. """
flags.DEFINE_float('learning_rate', 0.001, 'Initial learning rate.')

# For training and validating.
flags.DEFINE_integer('gpu', -1, 'Which gpu to use.')  # -1: cpu
flags.DEFINE_integer('iters', 10000, 'Number of iterations to train.')
flags.DEFINE_integer('iters_val_start', 9000,
                     'Number of iterations to start validation.')
flags.DEFINE_integer('iters_val_every', 50, 'Frequency of validation.')
if need_gc:
    flags.DEFINE_integer('iters_gc_start', 15000,
                         'Number of iterations to start '
                         'introducing graph classification for training.')
    flags.DEFINE_string('gc_bert_or_semi', 'bert',
                         'bert: fine-tune (only gc loss at the 2nd stage);'
                         'semi: semi-supervised (gc_loss + other_loss at the 2nd stage)')
flags.DEFINE_boolean('need_gc', need_gc,
                     'Whether to do graph classification or not.')

# For testing.
flags.DEFINE_boolean('plot_results', True,
                     'Whether to plot the results '
                     '(involving all baselines) or not.')
flags.DEFINE_integer('plot_max_num', 10, 'Max number of plots per experiment.')
if dataset_super_large:
    # Super large dataset: test strategies.
    flags.DEFINE_integer('slt_cat_num', 0, '')
    # 5 real graphs (random), from each generating 10 iso top graphs.
    # flags.DEFINE_string('slt_cat_1_from', '10_testgs', '')
    # flags.DEFINE_string('slt_cat_1_gen', '20_isotop_10%', '')
    # # 5 re11al graphs (largest), from each doing small perturbations for 10 times.
    # flags.DEFINE_string('slt_cat_1_from', '1_testgs_largest', '')
    # flags.DEFINE_string('slt_cat_1_gen', '50_sp', '')
    # # 5 artificial graphs, from each removing 1%, 2%, ..., 10% edges.
    # flags.DEFINE_string('slt_cat_1_from', '1_randomedge_10', '')
    # flags.DEFINE_string('slt_cat_1_gen', '1_randomedge_1000', '')
    # flags.DEFINE_string('slt_cat_1_from', '1_randomedge_10', '')
    # flags.DEFINE_string('slt_cat_1_gen', '1_randomedge_10000', '')
    # flags.DEFINE_string('slt_cat_1_from', '10_randomedge_10', '')
    # flags.DEFINE_string('slt_cat_1_gen', '10_randomedge_4096', '')
    # flags.DEFINE_string('slt_cat_4_from', '1_randomedge_10', '')
    # flags.DEFINE_string('slt_cat_4_gen', '1_randomedge_1000000', '')
    # flags.DEFINE_string('slt_cat_5_from', '1_randomedge_10', '')
    # flags.DEFINE_string('slt_cat_5_gen', '1_randomedge_10000000', '')
    max_nodes += 4096
flags.DEFINE_integer('max_nodes', max_nodes, 'Maximum number of nodes in a graph.')

FLAGS = tf.app.flags.FLAGS