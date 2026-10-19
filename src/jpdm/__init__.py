"""Joint-production displacement model (jpdm).

A nested equilibrium displacement model of animal-product markets with joint products, floors and price caps.
It estimates how much animal production falls when demand for one product of an animal (cheese, whey protein,
shell eggs, egg white, chicken breast, ground beef and so on) is replaced.

    from jpdm import params
    cow = params.dairy("2026")
    cow.DF_stream("Cheese", cow.eps_s_lr)      # displacement factor after three to five years

Run `python -m jpdm --help` for the command line.
"""
__version__ = "1.0.0"

from . import edm_model, params, exact_model  # noqa: F401
