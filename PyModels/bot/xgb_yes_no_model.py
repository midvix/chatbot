# -*- coding: utf-8 -*-

import os
import json
import logging
import xgboost
from scipy.sparse import lil_matrix

from yes_no_model import YesNoModel


class XGB_YesNoModel(YesNoModel):
    def __init__(self):
        super(XGB_YesNoModel, self).__init__()
        self.logger = logging.getLogger('XGB_YesNoModel')

    def load(self, models_folder):
        self.logger.info('Loading XGB_YesNoModel model files')

        with open(os.path.join(models_folder, 'xgb_yes_no.config'), 'r') as f:
            model_config = json.load(f)

        self.xgb_yesno_shingle2id = model_config['shingle2id']
        self.xgb_yesno_shingle_len = model_config['shingle_len']
        self.xgb_yesno_nb_features = model_config['nb_features']
        self.xgb_yesno_feature_names = model_config['feature_names']
        self.xgb_yesno = xgboost.Booster()
        self.xgb_yesno.load_model( self.get_model_filepath( models_folder,  model_config['model_filename'] ) )

    def xgb_yesno_vectorize_sample_x(self, X_data, idata, premise_shingles, question_shingles, shingle2id):
        ps = set(premise_shingles)
        qs = set(question_shingles)
        common_shingles = ps & qs
        notmatched_ps = ps - qs
        notmatched_qs = qs - ps

        nb_shingles = len(shingle2id)

        icol = 0
        for shingle in common_shingles:
            if shingle not in shingle2id:
                print(u'Missing shingle {} in yes_no data'.format(shingle))
            X_data[idata, icol + shingle2id[shingle]] = True

        icol += nb_shingles
        for shingle in notmatched_ps:
            X_data[idata, icol + shingle2id[shingle]] = True

        icol += nb_shingles
        for shingle in notmatched_qs:
            X_data[idata, icol + shingle2id[shingle]] = True

    def calc_yes_no(self, premise_words, question_words, text_utils, word_embeddings):
        premise_wx = text_utils.words2str(premise_words)
        question_wx = text_utils.words2str(question_words)

        premise_shingles = set(text_utils.ngrams(premise_wx, self.xgb_yesno_shingle_len))
        question_shingles = set(text_utils.ngrams(question_wx, self.xgb_yesno_shingle_len))

        X_data = lil_matrix((1, self.xgb_yesno_nb_features), dtype='bool')
        self.xgb_yesno_vectorize_sample_x(X_data, 0, premise_shingles, question_shingles, self.xgb_yesno_shingle2id)

        D_data = xgboost.DMatrix(X_data, feature_names=self.xgb_yesno_feature_names)
        y = self.xgb_yesno.predict(D_data)[0]
        return y

