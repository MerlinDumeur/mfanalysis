from dataclasses import dataclass, InitVar, field

import numpy as np
import matplotlib.pyplot as plt

from .utils import linear_regression, fast_power
from .multiresquantity import MultiResolutionQuantityBase,\
    MultiResolutionQuantity


@dataclass
class StructureFunction(MultiResolutionQuantityBase):
    """
    Computes and analyzes structure functions

    Parameters
    ----------
    mrq : MultiResolutionQuantity
        Multi resolution quantity to analyze.
    q : ndarray, shape (n_exponents,)
        Exponent for which to compute the structure function
    j1 : int
        Lower-bound of the scale support for the linear regressions.
    j2 : int
        Upper-bound of the scale support for the linear regressions.
    wtype: bool
        Whether to used weighted linear regressions.

    Attributes
    ----------
    formalism : str
        Formalism used. Can be any of 'wavelet coefs', 'wavelet leaders',
        or 'wavelet p-leaders'.
    nj : dict
        Number of coefficients at scale j.
    j : ndarray, shape (n_scales,)
        List of the j values (scales), in order presented in the value arrays.
    j1 : int
        Lower-bound of the scale support for the linear regressions.
    j2 : int
        Upper-bound of the scale support for the linear regressions.
    wtype : bool
        Whether weighted regression was performed.
    q : ndarray, shape (n_exponents,)
        Exponents for which the structure functions have been computed
    values : ndarray, shape (n_exponents, n_scales)
        Structure functions : :math:`S(j, q)`
    logvalues : ndarray, shape (n_exponents, n_scales)
        :math:`\\log_2 S(j, q)`
    zeta : ndarray, shape(n_exponents)
        Scaling function : :math:`\\zeta(q)`

    """
    mrq: InitVar[MultiResolutionQuantity]
    q: np.array
    j1: int
    j2: int
    wtype: bool
    j: np.array = field(init=False)
    values: np.ndarray = field(init=False)
    logvalues: np.array = field(init=False)
    zeta: np.array = field(init=False)

    def __post_init__(self, mrq):

        self.name = mrq.name
        self.j = np.array(list(mrq.values))

        self._compute(mrq)
        self._compute_zeta(mrq)

    def _compute(self, mrq):

        values = np.zeros((len(self.q), len(self.j)))

        for ind_j, j in enumerate(self.j):

            c_j = mrq.values[j]
            s_j = np.zeros(values.shape[0])

            for ind_q, q in enumerate(self.q):
                s_j[ind_q] = np.mean(fast_power(np.abs(c_j), q))

            values[:, ind_j] = s_j

        self.logvalues = np.log2(values)

    def _compute_zeta(self, mrq):
        """
        Compute the value of the scale function zeta(q) for all q
        """
        self.zeta = np.zeros(len(self.q))
        self.intercept = np.zeros(len(self.q))

        x = np.arange(self.j1, self.j2+1)

        if self.wtype:
            nj = mrq.get_nj_interv(self.j1, self.j2)
        else:
            nj = np.ones(len(x))

        ind_j1 = self.j1-1
        ind_j2 = self.j2-1
        for ind_q in range(len(self.q)):
            y = self.logvalues[ind_q, ind_j1:ind_j2+1]
            slope, intercept = linear_regression(x, y, nj)
            self.zeta[ind_q] = slope
            self.intercept[ind_q] = intercept

    def get_H(self):
        H = self.zeta[self.q == 2]

        if len(H) > 0:
            return H[0] / 2

        return None

    def get_intercept(self):
        intercept = self.intercept[self.q == 2]

        if len(intercept) > 0:
            return intercept[0]

        return None

    def plot(self, figlabel='Structure Functions', nrow=4, filename=None,
             ignore_q0=True):
        """
        Plots the structure functions.
        Args:
        fignum(int):  figure number; NOTE: fignum+1 can also be used to plot
        the scaling function
        """

        nrow = min(nrow, len(self.q))
        nq = len(self.q) + (-1 if 0.0 in self.q and ignore_q0 else 0)

        if nq > 1:
            plot_dim_1 = nrow
            plot_dim_2 = int(np.ceil(nq / nrow))

        else:
            plot_dim_1 = 1
            plot_dim_2 = 1

        fig, axes = plt.subplots(plot_dim_1,
                                 plot_dim_2,
                                 num=figlabel,
                                 squeeze=False,
                                 figsize=(30, 10))

        fig.suptitle(self.formalism +
                     r' - structure functions $\log_2(S(j,q))$')

        x = self.j
        for ind_q, q in enumerate(self.q):

            if q == 0.0 and ignore_q0:
                continue

            y = self.logvalues[ind_q, :]

            ax = axes[ind_q % nrow][ind_q // nrow]
            ax.plot(x, y, 'r--.')
            ax.set_xlabel('j')
            ax.set_ylabel(f'q = {q:.3f}')
            # ax.grid()
            # plt.draw()

            if len(self.zeta) > 0:
                # plot regression line
                x0 = self.j1
                x1 = self.j2
                slope = self.zeta[ind_q]
                intercept = self.intercept[ind_q]
                y0 = slope*x0 + intercept
                y1 = slope*x1 + intercept
                legend = 'slope = '+'%.5f' % (slope)

                ax.plot([x0, x1], [y0, y1], color='k',
                        linestyle='-', linewidth=2, label=legend)
                ax.legend()

        for j in range(ind_q + 1, len(axes.flat)):
            fig.delaxes(axes[j % nrow][j // nrow])
        plt.draw()

        if filename is not None:
            plt.savefig(filename)

    def plot_scaling(self, figlabel='Scaling Function', filename=None):

        assert len(self.q) > 1, ("This plot is only possible if more than 1 q",
                                 " value is used")

        plt.figure(figlabel)
        plt.plot(self.q, self.zeta, 'k--.')
        plt.xlabel('q')
        plt.ylabel(r'$\zeta(q)$')
        plt.suptitle(self.formalism + ' - scaling function')
        # plt.grid()

        plt.draw()

        if filename is not None:
            plt.savefig(filename)
