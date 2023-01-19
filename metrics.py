import numpy as np
import torch
import torch.nn as nn
from kuma_utils.metrics import MetricTemplate


class Pfbeta(nn.Module):
    '''
    '''
    def __init__(self, binarize=True, return_thres=False, average_both=False):
        super().__init__()
        self.return_thres = return_thres
        self.bin = binarize
        self.avg_both = average_both

    def pfbeta(self, labels, predictions, beta=1.):
        if len(labels.shape) == 2:
            labels = labels.reshape(-1)
        if len(predictions.shape) == 2:
            predictions = predictions.reshape(-1)
        y_true_count = 0
        ctp = 0
        cfp = 0

        for idx in range(len(labels)):
            prediction = min(max(predictions[idx], 0), 1)
            if (labels[idx]):
                y_true_count += 1
                ctp += prediction
            else:
                cfp += prediction

        beta_squared = beta * beta
        if ctp + cfp == 0:
            return 0
        c_precision = ctp / (ctp + cfp)
        c_recall = ctp / y_true_count
        if (c_precision > 0 and c_recall > 0):
            result = (1 + beta_squared) * (c_precision * c_recall) / (beta_squared * c_precision + c_recall)
            return result
        else:
            return 0

    def optimal_f1(self, labels, predictions):
        thres = np.linspace(0, 1, 101)
        f1s = [self.pfbeta(labels, predictions > thr) for thr in thres]
        idx = np.argmax(f1s)
        return f1s[idx], thres[idx]

    def optimal_f1_all(self, labels, predictions):
        thres = np.linspace(0, 1, 101)
        f1s = [self.pfbeta(labels, predictions > thr) for thr in thres]
        return f1s, thres

    def forward(self, approx, target):
        if isinstance(approx, torch.Tensor):
            approx = approx.sigmoid().detach().cpu().numpy()
            target = target.detach().cpu().numpy()
        if self.avg_both:
            f1s, thres = self.optimal_f1(target, approx)
            bin_score = f1s
            score = self.pfbeta(target, approx)
            return (bin_score + score) / 2
        elif self.bin: # search for best binarization threshold
            f1s, thres = self.optimal_f1(target, approx)
            if self.return_thres:
                return f1s, thres
            else:
                return f1s
        else:
            return self.pfbeta(target, approx)

