#!/usr/bin/env python

import numpy as np


class checkCompletion(object):
    """completion checkers
    """

    def __init__(self, apSN2=None, epoch_apSN2=None,
                 bSN2=None, epoch_bSN2=None,
                 rSN2=None, epoch_rSN2=None):
        if apSN2 is None:
            assert bSN2 is not None, "must specify sn2"
            assert rSN2 is not None, "must specify sn2"
            assert epoch_bSN2 is not None, "must specify sn2"
            assert epoch_rSN2 is not None, "must specify sn2"

        self.apSN2 = apSN2
        self.bSN2 = bSN2
        self.rSN2 = rSN2
        self.epoch_apSN2 = epoch_apSN2
        self.epoch_bSN2 = epoch_bSN2
        self.epoch_rSN2 = epoch_rSN2

    def design(self, ap=None, b=None, r=None):
        # epects summed sn2 for a design
        if self.apSN2:
            if ap > self.apSN2:
                return True
        else:
            if b > self.bSN2 and r > self.rSN2:
                return True

    def epoch(self, ap=None, b=None, r=None, N=1):
        # N for e.g. dark faint completion scales with N exposures
        if self.apSN2:
            if np.sum(ap) > self.epoch_apSN2 * N:
                return True
        else:
            bSN2 = np.sum(b)
            rSN2 = np.sum(r)
            if bSN2 > self.epoch_bSN2 * N and rSN2 > self.epoch_rSN2 * N:
                return True


bright_time = checkCompletion(apSN2=2025, epoch_apSN2=2025)

dark_plane = checkCompletion(bSN2=1.5, epoch_bSN2=5,
                             rSN2=3, epoch_rSN2=10)

dark_monit = checkCompletion(bSN2=1.5, epoch_bSN2=10,
                             rSN2=3, epoch_rSN2=20)

dark_rm = checkCompletion(bSN2=1.5, epoch_bSN2=20,
                          rSN2=3, epoch_rSN2=40)

dark_faint = checkCompletion(bSN2=1.5, epoch_bSN2=2.5,
                             rSN2=3, epoch_rSN2=5)
checker = {
    "bright_time": bright_time,
    "dark_plane": dark_plane,
    "dark_monit": dark_monit,
    "dark_rm": dark_rm,
    "dark_faint": dark_faint
}
