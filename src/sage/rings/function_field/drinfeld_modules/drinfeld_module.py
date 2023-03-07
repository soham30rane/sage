r"""
Drinfeld modules

This module provides the class
:class:`sage.rings.function_field.drinfeld_module.drinfeld_module.DrinfeldModule`.

For finite Drinfeld modules and their theory of complex multiplication, see
class
:class:`sage.rings.function_field.drinfeld_module.finite_drinfeld_module.DrinfeldModule`.

AUTHORS:

- Antoine Leudière (2022-04): initial version
- Xavier Caruso (2022-06): initial version
- David Ayotte (2023-03): added basic `j`-invariants
"""

# *****************************************************************************
#        Copyright (C) 2022 Antoine Leudière <antoine.leudiere@inria.fr>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#                   http://www.gnu.org/licenses/
# *****************************************************************************

from sage.arith.misc import gcd
from sage.categories.drinfeld_modules import DrinfeldModules
from sage.categories.homset import Hom
from sage.geometry.polyhedron.constructor import Polyhedron
from sage.misc.latex import latex
from sage.misc.latex import latex_variable_name
from sage.misc.lazy_string import _LazyString
from sage.misc.misc_c import prod
from sage.rings.integer import Integer
from sage.rings.polynomial.ore_polynomial_element import OrePolynomial
from sage.rings.polynomial.polynomial_ring import PolynomialRing_general
from sage.rings.ring_extension import RingExtension_generic
from sage.structure.parent import Parent
from sage.structure.sage_object import SageObject
from sage.structure.sequence import Sequence
from sage.structure.unique_representation import UniqueRepresentation


class DrinfeldModule(Parent, UniqueRepresentation):
    r"""
    This class implements Drinfeld `\mathbb{F}_q[T]`-modules.

    Let `\mathbb{F}_q[T]` be a polynomial ring with coefficients in a
    finite field `\mathbb{F}_q` and let `K` be a field. Fix a ring
    morphism `\gamma: \mathbb{F}_q[T] \to K`; we say that `K` is an
    `\mathbb{F}_q[T]`-*field*. Let `K\{\tau\}` be the ring of Ore
    polynomials with coefficients in `K`, whose multiplication is given
    by the rule `\tau \lambda = \lambda^q \tau` for any `\lambda \in K`.

    A Drinfeld `\mathbb{F}_q[T]`-module over the base
    `\mathbb{F}_q[T]`-field `K` is an `\mathbb{F}_q`-algebra morphism
    `\phi: \mathbb{F}_q[T] \to K\{\tau\}` such that `\mathrm{Im}(\phi)
    \not\subset K` and `\phi` agrees with `\gamma` on `\mathbb{F}_q`.

    For `a` in `\mathbb{F}_q[T]`, `\phi(a)` is denoted `\phi_a`.

    The Drinfeld `\mathbb{F}_q[T]`-module `\phi` is uniquely determined
    by the image `\phi_T` of `T`; this serves as input of the class.

    .. NOTE::

        See also :class:`sage.categories.drinfeld_modules`.

    The *base morphism* is the morphism `\gamma: \mathbb{F}_q[T] \to K`.
    The monic polynomial that generates the kernel of `\gamma` is called
    the `\mathbb{F}_q[T]`-*characteristic*, or *function-field
    characteristic*, of the base field. We say that `\mathbb{F}_q[T]` is
    the *function ring* of `\phi`; `K\{\tau\}` is the *Ore polynomial
    ring*. Further, the *generator* is `\phi_T` and the *constant
    coefficient* is the constant coefficient of `\phi_T`.

    A Drinfeld module is said to be *finite* if the field `K` is.
    Despite an emphasis on this case, the base field can be any
    extension of `\mathbb{F}_q`::

        sage: Fq = GF(25)
        sage: A.<T> = Fq[]
        sage: K.<z> = Fq.extension(6)
        sage: phi = DrinfeldModule(A, [z, 4, 1])
        sage: phi
        Drinfeld module defined by T |--> t^2 + 4*t + z

    ::

        sage: Fq = GF(49)
        sage: A.<T> = Fq[]
        sage: K = Frac(A)
        sage: psi = DrinfeldModule(A, [K(T), T+1])
        sage: psi
        Drinfeld module defined by T |--> (T + 1)*t + T

    .. NOTE::

        Finite Drinfeld modules are implemented in the class
        :class:`sage.rings.function_field.drinfeld_modules.finite_drinfeld_module`.

    Classical references on Drinfeld modules include [Gos1998]_,
    [Rosen2002]_, [VS06]_ and [Gek1991]_.

    .. NOTE::

        Drinfeld modules are defined in a larger setting, in which the
        polynomial ring `\mathbb{F}_q[T]` is replaced by a more general
        function ring: the ring of functions in `k` that are regular
        outside `\infty`, where `k` is a function field over
        `\mathbb{F}_q` with transcendence degree `1` and `\infty` is a
        fixed place of `k`. This is out of the scope of this
        implementation.

    INPUT:

    - ``function_ring`` -- a univariate polynomial ring whose base field
      is a finite field

    - ``gen`` -- the generator of the Drinfeld module; as a list of
      coefficients or an Ore polynomial

    - ``name`` (default: ``'t'``) -- the name of the Ore polynomial ring
      generator

    .. RUBRIC:: Construction

    A Drinfeld module object is constructed by giving the function ring
    and the generator::

        sage: Fq.<z2> = GF(3^2)
        sage: A.<T> = Fq[]
        sage: K.<z> = Fq.extension(6)
        sage: phi = DrinfeldModule(A, [z, 1, 1])
        sage: phi
        Drinfeld module defined by T |--> t^2 + t + z

    .. NOTE::

        Note that the definition of the base field is implicit; it is
        automatically defined as the compositum of all the parents of
        the coefficients.

    The above Drinfeld module is finite; it can also be infinite::

        sage: L = Frac(A)
        sage: psi = DrinfeldModule(A, [L(T), 1, T^3 + T + 1])
        sage: psi
        Drinfeld module defined by T |--> (T^3 + T + 1)*t^2 + t + T

    ::

        sage: phi.is_finite()
        True
        sage: psi.is_finite()
        False

    In those examples, we used a list of coefficients (``[z, 1, 1]``) to
    represent the generator `\phi_T = z + t + t^2`. One can also use
    regular Ore polynomials::

        sage: ore_polring = phi.ore_polring()
        sage: t = ore_polring.gen()
        sage: rho_T = z + t^3
        sage: rho = DrinfeldModule(A, rho_T)
        sage: rho
        Drinfeld module defined by T |--> t^3 + z
        sage: rho(T) == rho_T
        True

    Images under the Drinfeld module are computed by calling the object::

        sage: phi(T)  # phi_T, the generator of the Drinfeld module
        t^2 + t + z
        sage: phi(T^3 + T + 1)  # phi_(T^3 + T + 1)
        t^6 + (z^11 + z^9 + 2*z^6 + 2*z^4 + 2*z + 1)*t^4 + (2*z^11 + 2*z^10 + z^9 + z^8 + 2*z^7 + 2*z^6 + z^5 + 2*z^3)*t^3 + (2*z^11 + z^10 + z^9 + 2*z^7 + 2*z^6 + z^5 + z^4 + 2*z^3 + 2*z + 2)*t^2 + (2*z^11 + 2*z^8 + 2*z^6 + z^5 + z^4 + 2*z^2)*t + z^3 + z + 1
        sage: phi(1)  # phi_1
        1

    .. RUBRIC:: The category of Drinfeld modules

    Drinfeld modules have their own category (see class
    :class:`sage.categories.drinfeld_modules.DrinfeldModules`)::

        sage: phi.category()
        Category of Drinfeld modules over Finite Field in z of size 3^12 over its base
        sage: phi.category() is psi.category()
        False
        sage: phi.category() is rho.category()
        True

    One can use the category to directly create new objects::

        sage: cat = phi.category()
        sage: cat.object([z, 0, 0, 1])
        Drinfeld module defined by T |--> t^3 + z

    .. RUBRIC:: The base field of a Drinfeld module

    The base field of the Drinfeld module is retrieved using :meth:`base`::

        sage: phi.base()
        Finite Field in z of size 3^12 over its base

    The base morphism is retrieved using :meth:`base_morphism`::

        sage: phi.base_morphism()
        Ring morphism:
          From: Univariate Polynomial Ring in T over Finite Field in z2 of size 3^2
          To:   Finite Field in z of size 3^12 over its base
          Defn: T |--> z

    Note that the base field is *not* the field `K`. Rather, it is a ring
    extension (see :class:`sage.rings.ring_extension.RingExtension`) whose
    underlying ring is `K` and whose base is the base morphism::

        sage: phi.base() is K
        False

    .. RUBRIC:: Getters

    One can retrieve basic properties::

        sage: phi.base_morphism()
        Ring morphism:
          From: Univariate Polynomial Ring in T over Finite Field in z2 of size 3^2
          To:   Finite Field in z of size 3^12 over its base
          Defn: T |--> z

    ::

        sage: phi.ore_polring()  # K{t}
        Ore Polynomial Ring in t over Finite Field in z of size 3^12 over its base twisted by Frob^2

    ::

        sage: phi.function_ring()  # Fq[T]
        Univariate Polynomial Ring in T over Finite Field in z2 of size 3^2

    ::

        sage: phi.gen()  # phi_T
        t^2 + t + z
        sage: phi.gen() == phi(T)
        True

    ::

        sage: phi.constant_coefficient()  # Constant coefficient of phi_T
        z

    ::

        sage: phi.morphism()  # The Drinfeld module as a morphism
        Ring morphism:
          From: Univariate Polynomial Ring in T over Finite Field in z2 of size 3^2
          To:   Ore Polynomial Ring in t over Finite Field in z of size 3^12 over its base twisted by Frob^2
          Defn: T |--> t^2 + t + z

    One can compute the rank and height::

        sage: phi.rank()
        2
        sage: phi.height()
        1

    As well as the j-invariant::

        sage: phi.j_invariant()  # j-invariant
        1

    A Drinfeld `\mathbb{F}_q[T]`-module can be seen as an Ore polynomial
    with positive degree and constant coefficient `\gamma(T)`, where
    `\gamma` is the base morphism. This analogy is the motivation for
    the following methods::

        sage: phi.coefficients()
        [z, 1, 1]

    ::

        sage: phi.coefficient(1)
        1


    .. RUBRIC:: Morphisms and isogenies

    A *morphism* of Drinfeld modules `\phi \to \psi` is an Ore
    polynomial `f \in K\{\tau\}` such that `f \phi_a = \psi_a f` for
    every `a` in the function ring. In our case, this is equivalent to
    `f \phi_T = \psi_T f`. An *isogeny* is a nonzero morphism.

    Use the ``in`` syntax to test if an Ore polynomial defines a
    morphism::

        sage: phi(T) in Hom(phi, phi)
        True
        sage: t^6 in Hom(phi, phi)
        True
        sage: t^5 + 2*t^3 + 1 in Hom(phi, phi)
        False
        sage: 1 in Hom(phi, rho)
        False
        sage: 1 in Hom(phi, phi)
        True
        sage: 0 in Hom(phi, rho)
        True

    To create a SageMath object representing the morphism, call the
    homset (``hom``)::

        sage: hom = Hom(phi, phi)
        sage: frobenius_endomorphism = hom(t^6)
        sage: identity_morphism = hom(1)
        sage: zero_morphism = hom(0)
        sage: frobenius_endomorphism
        Endomorphism of Drinfeld module defined by T |--> t^2 + t + z
          Defn: t^6
        sage: identity_morphism
        Identity morphism of Drinfeld module defined by T |--> t^2 + t + z
        sage: zero_morphism
        Endomorphism of Drinfeld module defined by T |--> t^2 + t + z
          Defn: 0

    The underlying Ore polynomial is retrieved with the method
    :meth:`ore_polynomial`::

        sage: frobenius_endomorphism.ore_polynomial()
        t^6
        sage: identity_morphism.ore_polynomial()
        1

    One checks if a morphism is an isogeny, endomorphism or
    isomorphism::

        sage: frobenius_endomorphism.is_isogeny()
        True
        sage: identity_morphism.is_isogeny()
        True
        sage: zero_morphism.is_isogeny()
        False
        sage: frobenius_endomorphism.is_isomorphism()
        False
        sage: identity_morphism.is_isomorphism()
        True
        sage: zero_morphism.is_isomorphism()
        False

    .. RUBRIC:: The Vélu formula

    Let ``P`` be a nonzero Ore polynomial. We can decide if ``P``
    defines an isogeny with a given domain and, if it does, find
    the codomain::

        sage: P = (2*z^6 + z^3 + 2*z^2 + z + 2)*t + z^11 + 2*z^10 + 2*z^9 + 2*z^8 + z^7 + 2*z^6 + z^5 + z^3 + z^2 + z
        sage: psi = phi.velu(P)
        sage: psi
        Drinfeld module defined by T |--> (2*z^11 + 2*z^9 + z^6 + 2*z^5 + 2*z^4 + 2*z^2 + 1)*t^2 + (2*z^11 + 2*z^10 + 2*z^9 + z^8 + 2*z^7 + 2*z^6 + z^5 + 2*z^4 + 2*z^2 + 2*z)*t + z
        sage: P in Hom(phi, psi)
        True
        sage: P * phi(T) == psi(T) * P
        True

    If the input does not define an isogeny, an exception is raised::

        sage: phi.velu(0)
        Traceback (most recent call last):
        ...
        ValueError: the input does not define an isogeny
        sage: phi.velu(t)
        Traceback (most recent call last):
        ...
        ValueError: the input does not define an isogeny

    .. RUBRIC:: The action of a Drinfeld module

    The `\mathbb{F}_q[T]`-Drinfeld module `\phi` induces a special left
    `\mathbb{F}_q[T]`-module structure on any field extension `L/K`. Let
    `x \in L` and `a` be in the function ring; the action is defined as
    `(a, x) \mapsto \phi_a(x)`. The method :meth:`action` returns a
    :class:`sage.rings.function_field.drinfeld_modules.action.Action`
    object representing the Drinfeld module action.

    .. NOTE::

        In this implementation, `L` is `K`::

            sage: action = phi.action()
            sage: action
            Action on Finite Field in z of size 3^12 over its base induced by Drinfeld module defined by T |--> t^2 + t + z

    The action on elements is computed by calling the action object::

        sage: P = T + 1
        sage: a = z
        sage: action(P, a)
        ...
        z^9 + 2*z^8 + 2*z^7 + 2*z^6 + 2*z^3 + z^2
        sage: action(0, K.random_element())
        0
        sage: action(A.random_element(), 0)
        0

    .. WARNING::

        The class ``DrinfeldModuleAction`` may be replaced later on. See
        issues #34833 and #34834.

    TESTS:

    The generator must have positive degree::

        sage: Fq = GF(2)
        sage: K.<z> = Fq.extension(2)
        sage: A.<T> = Fq[]
        sage: DrinfeldModule(A, [K(1)])
        Traceback (most recent call last):
        ...
        ValueError: generator must have positive degree

    The constant coefficient must be nonzero::

        sage: Fq = GF(2)
        sage: K.<z> = Fq.extension(2)
        sage: A.<T> = Fq[]
        sage: DrinfeldModule(A, [K(0), K(1)])
        Traceback (most recent call last):
        ...
        ValueError: constant coefficient must be nonzero

    The coefficients of the generator must lie in an
    `\mathbb{F}_q[T]`-field, where `\mathbb{F}_q[T]` is the function
    ring of the Drinfeld module::

        sage: Fq = GF(2)
        sage: K.<z> = Fq.extension(2)
        sage: A.<T> = Fq[]
        sage: DrinfeldModule(A, [z, QQ(1)])
        Traceback (most recent call last):
        ...
        ValueError: function ring base must coerce into base field

    ::

        sage: Fq = GF(2)
        sage: K.<z> = Fq.extension(2)
        sage: A.<T> = Fq[]
        sage: DrinfeldModule(A, [1, QQ(1)])
        Traceback (most recent call last):
        ...
        ValueError: function ring base must coerce into base field

    The function ring must be an univariate polynomial ring whose
    base is a finite field::

        sage: Fq = GF(2)
        sage: K.<z> = Fq.extension(2)
        sage: A.<T> = Fq[]
        sage: DrinfeldModule(K, [z, 1, 1])
        Traceback (most recent call last):
        ...
        NotImplementedError: function ring must be a polynomial ring

    ::

        sage: Fq = GF(2)
        sage: K.<z> = Fq.extension(2)
        sage: A.<T> = Fq[]
        sage: AY.<Y> = A[]
        sage: DrinfeldModule(AY, [z, 1, 1])
        Traceback (most recent call last):
        ...
        TypeError: function ring base must be a finite field

    If you already defined a category of Drinfeld modules, and you
    create a Drinfeld module through this category, you must ensure that
    the constant coefficient is that of the category::

        sage: Fq = GF(2)
        sage: K.<z> = Fq.extension(2)
        sage: A.<T> = Fq[]
        sage: phi = DrinfeldModule(A, [z, 1])
        sage: phi.category().object([1, 1, K(1)])
        Traceback (most recent call last):
        ...
        ValueError: constant coefficient must equal that of the category

    ::

        sage: Fq = K = GF(2)
        sage: A.<T> = Fq[]
        sage: phi = DrinfeldModule(A, [1, 1])
        Traceback (most recent call last):
        ...
        ValueError: function ring base must coerce into base field

    ::

        sage: Fq = K = GF(2)
        sage: A.<T> = Fq[]
        sage: phi = DrinfeldModule(A, [K(1), 1])
        sage: isinstance(phi.ore_polring(), OrePolynomialRing)
        True
    """

    @staticmethod
    def __classcall_private__(cls, function_ring, gen, name='t'):
        """
        Check input validity and return a ``DrinfeldModule`` or
        ``FiniteDrinfeldModule`` object accordingly.

        INPUT:

        - ``function_ring`` -- a univariate polynomial ring whose base
          is a finite field

        - ``gen`` -- the generator of the Drinfeld module; as a list of
          coefficients or an Ore polynomial

        - ``name`` (default: ``'t'``) -- the name of the Ore polynomial
          ring gen

        OUTPUT:

        A DrinfeldModule or FiniteDrinfeldModule.

        TESTS::

            sage: from sage.rings.function_field.drinfeld_modules.finite_drinfeld_module import FiniteDrinfeldModule
            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: isinstance(phi, FiniteDrinfeldModule)
            True

        ::

            sage: K = Frac(A)
            sage: phi = DrinfeldModule(A, [K(T), 1])
            sage: isinstance(psi, FiniteDrinfeldModule)
            False
        """

        # FIXME: function_ring must be checked before calling base_ring
        # on it. But then it is checked twice: firstly here, secondly in
        # the category. Another problem is that those lines are
        # duplicate. As a general comment, there are sanity checks both
        # here and in the category constructor, which is not ideal.
        # Check domain is Fq[T]
        if not isinstance(function_ring, PolynomialRing_general):
            raise NotImplementedError('function ring must be a polynomial '
                                      'ring')
        function_ring_base = function_ring.base_ring()
        if not function_ring_base.is_field() \
                or not function_ring_base.is_finite():
            raise TypeError('function ring base must be a finite field')

        # Check all possible input types for gen
        # `gen` is an Ore polynomial:
        if isinstance(gen, OrePolynomial):
            ore_polring = gen.parent()
            # Base ring without morphism structure:
            base_field_noext = ore_polring.base()
            name = ore_polring.variable_name()
        # `gen` is a list of coefficients (function_ring = Fq[T]):
        elif isinstance(gen, (list, tuple)):
            ore_polring = None
            # Base ring without morphism structure:
            base_field_noext = Sequence(gen).universe()
        else:
            raise TypeError('generator must be list of coefficients or Ore '
                            'polynomial')
        # Constant coefficient must be nonzero:
        if gen[0].is_zero():
            raise ValueError('constant coefficient must be nonzero')
        # The coefficients are in a base field that has coercion from Fq:
        if not (hasattr(base_field_noext, 'has_coerce_map_from') and
                base_field_noext.has_coerce_map_from(function_ring.base_ring())):
            raise ValueError('function ring base must coerce into base field')

        # Build the category
        T = function_ring.gen()
        if isinstance(base_field_noext, RingExtension_generic):
            base_field = base_field_noext
        elif base_field_noext.has_coerce_map_from(function_ring) \
                and T == gen[0]:
            base_morphism = base_field_noext.coerce_map_from(function_ring)
            base_field = base_field_noext.over(base_morphism)
        else:
            base_morphism = Hom(function_ring, base_field_noext)(gen[0])
            base_field = base_field_noext.over(base_morphism)

        # This test is also done in the category. We put it here also
        # to have a friendlier error message
        if not base_field.is_field():
            raise ValueError('generator coefficients must live in a field')

        category = DrinfeldModules(base_field, name=name)

        # Check gen as Ore polynomial
        ore_polring = category.ore_polring()  # Sanity cast
        gen = ore_polring(gen)
        if gen.degree() <= 0:
            raise ValueError('generator must have positive degree')

        # Instantiate the appropriate class
        if base_field.is_finite():
            from sage.rings.function_field.drinfeld_modules.finite_drinfeld_module import FiniteDrinfeldModule
            return FiniteDrinfeldModule(gen, category)
        return cls.__classcall__(cls, gen, category)

    def __init__(self, gen, category):
        """
        Initialize ``self``.

        Validity of the input is checked in meth:`__classcall_private__`.
        The meth:`__init__` just saves attributes.

        INPUT:

        - ``function_ring`` -- a univariate polynomial ring whose base
          is a finite field

        - ``gen`` -- the generator of the Drinfeld module; as a list of
          coefficients or an Ore polynomial

        - ``name`` (default: ``'t'``) -- the name of the Ore polynomial
          ring gen

        TESTS::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: gen = [p_root, z12^3, z12^5]
            sage: phi = DrinfeldModule(A, gen)
            sage: ore_polring = phi.ore_polring()
            sage: phi._base == phi.category().base()
            True
            sage: phi._function_ring == A
            True
            sage: phi._gen == ore_polring(gen)
            True
            sage: phi._ore_polring == ore_polring
            True
            sage: phi._morphism == Hom(A, ore_polring)(phi._gen)
            True

        ::

            sage: TestSuite(phi).run()
        """
        self._base = category.base()
        self._function_ring = category.function_ring()
        self._gen = gen
        self._morphism = category._function_ring.hom([gen])
        self._ore_polring = gen.parent()
        self._Fq = self._function_ring.base_ring()  # Must be last
        super().__init__(base=self._base, category=category)

    def __call__(self, a):
        r"""
        Return the image of input ``a`` by the morphism that defines the
        Drinfeld module; i.e. `\phi_a` if the Drinfeld module is denoted
        `phi`.

        INPUT:

        - ``a`` -- a function ring element

        OUTPUT: an element in the base codomain

        TESTS::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])

        ::
            sage: a = T^3 + 4*T + 2
            sage: phi(a) == phi(T)^3 + 4*phi(T) + 2
            True
            sage: phi(a)[0] == p_root^3 + 4*p_root + 2
            True

        ::

            sage: phi(0)
            0
            sage: phi(1)
            1
            sage: phi(T) == phi._gen
            True

        ::

            sage: a = A.random_element(5)
            sage: phi(a)[0] == phi.category().base()(a)
            True
        """
        return self._morphism(a)

    def _Hom_(self, other, category):
        r"""
        Return ``DrinfeldModuleHomset(self, other, category)``.

        Validity of the input is checked at the instantiation of
        ``DrinfeldModuleHomset``. ``self`` and ``other`` only need be in
        the same category.

        INPUT:

        - ``other`` -- the codomain of the homset

        - ``category`` -- the category in which we consider the
          morphisms, usually ``self.category()``

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: t = phi.ore_polring().gen()
            sage: isog = t + 2*z12^11 + 4*z12^9 + 2*z12^8 + 2*z12^6 + 3*z12^5 + z12^4 + 2*z12^3 + 4*z12^2 + 4*z12 + 4
            sage: psi = phi.velu(isog)
            sage: hom = phi._Hom_(psi, category=phi.category())
            sage: hom is Hom(phi, psi)  # known bug
            True
            sage: from sage.rings.function_field.drinfeld_modules.homset import DrinfeldModuleHomset
            sage: isinstance(hom, DrinfeldModuleHomset)
            True
        """
        from sage.rings.function_field.drinfeld_modules.homset import DrinfeldModuleHomset
        return DrinfeldModuleHomset(self, other, category)

    def _check_rank_two(self):
        r"""
        Raise ``NotImplementedError`` if the rank is not two.

        TESTS::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi._check_rank_two()
            sage: phi = DrinfeldModule(A, [p_root, 1])
            sage: phi._check_rank_two()
            Traceback (most recent call last):
            ...
            NotImplementedError: rank must be 2
        """
        if self.rank() != 2:
            raise NotImplementedError('rank must be 2')

    def _latex_(self):
        r"""
        Return a LaTeX representation of the Drinfeld module.

        If a representation name is given with meth:`rename`, it is
        taken into account for LaTeX representation.

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: latex(phi)
            \phi: T \mapsto z_{12}^{5} t^{2} + z_{12}^{3} t + 2 z_{12}^{11} + 2 z_{12}^{10} + z_{12}^{9} + 3 z_{12}^{8} + z_{12}^{7} + 2 z_{12}^{5} + 2 z_{12}^{4} + 3 z_{12}^{3} + z_{12}^{2} + 2 z_{12}

        ::

            sage: phi.rename('phi')
            sage: latex(phi)
            \phi
            sage: phi.reset_name()
        """
        if hasattr(self, '__custom_name'):
            return latex_variable_name(getattr(self, '__custom_name'))
        else:
            return f'\\phi: {latex(self._function_ring.gen())} \\mapsto ' \
                   f'{latex(self._gen)}'

    def _repr_(self):
        r"""
        Return a string representation of this Drinfeld module.

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi
            Drinfeld module defined by T |--> z12^5*t^2 + z12^3*t + 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
        """
        return f'Drinfeld module defined by {self._function_ring.gen()} ' \
               f'|--> {self._gen}'

    def _test_category(self, **options):
        """
        Run generic tests on the method :meth:`.category`.

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi._test_category()

        .. NOTE::

            We reimplemented this method because Drinfeld modules are
            parents, and
            meth:`sage.structure.parent.Parent._test_category` requires
            parents' categories to be subcategories of ``Sets()``.
        """
        tester = self._tester(**options)
        SageObject._test_category(self, tester=tester)
        category = self.category()
        # Tests that self inherits methods from the categories
        tester.assertTrue(isinstance(self, category.parent_class),
                _LazyString("category of %s improperly initialized", (self,), {}))

    def __hash__(self):
        r"""
        Return a hash of ``self``.

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: hash(phi)  # random
            -6894299335185957188
        """
        return hash((self.base(), self._gen))

    def action(self):
        r"""
        Return the action object
        (:class:`sage.rings.function_field.drinfeld_modules.action.Action`)
        that represents the module action, on the base codomain, that is
        induced by the Drinfeld module.

        OUTPUT: a Drinfeld module action object

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: action = phi.action()
            sage: action
            Action on Finite Field in z12 of size 5^12 over its base induced by Drinfeld module defined by T |--> z12^5*t^2 + z12^3*t + 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12

        The action on elements is computed as follows::

            sage: P = T^2 + T + 1
            sage: a = z12 + 1
            sage: action(P, a)
            3*z12^11 + 2*z12^10 + 3*z12^9 + 3*z12^7 + 4*z12^5 + z12^4 + z12^3 + 2*z12 + 1
            sage: action(0, a)
            0
            sage: action(P, 0)
            0
        """
        from sage.rings.function_field.drinfeld_modules.action import DrinfeldModuleAction
        return DrinfeldModuleAction(self)

    def basic_j_invariant_parameters(self, coeff_indices=None, nonzero=False):
        r"""
        Return the list of basic `j`-invariant parameters.

        See the method :meth:`j_invariant` for the definition of the basic
        `j`-invariant parameters.

        INPUT:

        - ``coeff_indices`` (list or tuple, default: ``None``) -- a list or a
          tuple of indices for the coefficients of the Drinfeld module. If
          this option is not ``None``, then the method will return only the basic
          `j`-invariant parameters that involves the given indices. By default,
          the method will use all the coefficients.

        - ``nonzero`` (bool, Default: ``False``) -- setting this to ``True``
          will return only the parameters for which the basic `j`-invariant is
          nonzero

        .. WARNING::

            The usage of this method can be very computationally expensive
            depending if the given Drinfeld module is of rank strictly greater
            4 and for large value of `q`. Setting the ``nonzero`` flag to
            ``True`` can speed up the computation considerably if the Drinfeld
            module possesses multiple zero coefficients.

        EXAMPLES::

            sage: A = GF(5)['T']
            sage: K.<T> = Frac(A)
            sage: phi = DrinfeldModule(A, [T, 0, T+1, T^2 + 1])
            sage: phi.basic_j_invariant_parameters()
            [((1, 2), (1, 5, 1)),
             ((1, 2), (7, 4, 1)),
             ((1, 2), (13, 3, 1)),
             ((1, 2), (19, 2, 1)),
             ((1, 2), (25, 1, 1)),
             ((1, 2), (31, 0, 1)),
             ((1, 2), (8, 9, 2)),
             ((1, 2), (20, 7, 2)),
             ((1, 2), (9, 14, 3)),
             ((1, 2), (15, 13, 3)),
             ((1, 2), (27, 11, 3)),
             ((1, 2), (10, 19, 4)),
             ((1, 2), (22, 17, 4)),
             ((1, 2), (11, 24, 5)),
             ((1, 2), (17, 23, 5)),
             ((1, 2), (23, 22, 5)),
             ((1, 2), (29, 21, 5)),
             ((1, 2), (0, 31, 6)),
             ((1, 2), (12, 29, 6)),
             ((1, 2), (31, 31, 7))]

        If a list of indices is given, then only the parameters involving those
        coefficients will be computed::

            sage: A = GF(3)['T']
            sage: K.<T> = Frac(A)
            sage: phi = DrinfeldModule(A, [T, T, 2, T, 2*T, T^3, T^4 + T^2 + 1])
            sage: phi.basic_j_invariant_parameters([1, 5])
            [((1, 5), (273, 91, 31)),
             ((1, 5), (297, 163, 55)),
             ((1, 5), (295, 157, 53)),
             ((1, 5), (265, 67, 23)),
             ((1, 5), (357, 343, 115)),
             ...
             ((1, 5), (146, 74, 25))]

        Use ``nonzero=True`` to speed up the computations for Drinfeld modules
        for which some coefficients are zero::

            sage: A = GF(5)['T']
            sage: K.<T> = Frac(A)
            sage: phi = DrinfeldModule(A, [T, 0, T+1, 0, 1, 0, T])
            sage: phi.basic_j_invariant_parameters(nonzero=True)
            [((2, 4), (260, 641, 26)),
             ((2, 4), (157, 19, 1)),
             ((2, 4), (27, 24, 1)),
             ((2, 4), (188, 143, 6)),
             ((2, 4), (401, 260, 11)),
             ...
             ((2, 4), (288, 39, 2))]

        TESTS::

            sage: A = GF(5)['T']
            sage: K.<T> = Frac(A)
            sage: phi = DrinfeldModule(A, [T, 0, T+1, T^2 + 1])
            sage: phi.basic_j_invariant_parameters([1, 'x'])
            Traceback (most recent call last):
            ...
            TypeError: the elements of the list 'coeff_indices' must be integers
            sage: phi.basic_j_invariant_parameters([1, 10])
            Traceback (most recent call last):
            ...
            ValueError: the maximum or the minimum of the list coeff_indices must be > 0 and < 3 respectively
            sage: phi.basic_j_invariant_parameters([1, 1])
            Traceback (most recent call last):
            ...
            ValueError: the elements of coeff_indices should be distinct and sorted
            sage: phi.basic_j_invariant_parameters([2, 1])
            Traceback (most recent call last):
            ...
            ValueError: the elements of coeff_indices should be distinct and sorted
            sage: phi.basic_j_invariant_parameters('x')
            Traceback (most recent call last):
            ...
            TypeError: input 'coeff_indices' must be NoneType, a tuple or a list
        """
        r = self._gen.degree()
        if coeff_indices is None:
            if nonzero:
                coeff_indices = [k for k, g in enumerate(
                    self.coefficients(sparse=False)[1:-1], start=1) if g]
            else:
                coeff_indices = list(range(1, r))
        elif isinstance(coeff_indices, (tuple, list)):  # check if coeff_indices is valid
            coeff_indices = list(coeff_indices)
            if not all(isinstance(k, (int, Integer)) for k in coeff_indices):
                raise TypeError("the elements of the list 'coeff_indices' "
                                "must be integers")
            if max(coeff_indices) >= r or min(coeff_indices) <= 0:
                raise ValueError("the maximum or the minimum of the list "
                    f"coeff_indices must be > 0 and < {r} respectively")
            if not all(coeff_indices[i] < coeff_indices[i+1] for i in
                       range(len(coeff_indices) - 1)):
                raise ValueError("the elements of coeff_indices should be "
                                 "distinct and sorted")
            if nonzero:
                coeff_indices = [k for k in coeff_indices if self._gen[k]]
        else:
            raise TypeError("input 'coeff_indices' must be NoneType, a tuple "
                            "or a list")
        # Create the equation and inequalities for the polyhedron:
        q = self._Fq.order()
        equation = [0]
        inequalities = []
        for idx, i in enumerate(coeff_indices):
            # create the equation:
            #     d_1 (q - 1) + d_2 (q^2 - 1) + ... + d_{r-1} (q^{r-1} - 1) = d_r (q^r - 1)
            equation.append(q**i - 1)

            # create inequalities of the form 0 <= delta_i
            lower_bounds = [0]*(len(coeff_indices) + 2)
            lower_bounds[idx + 1] = 1

            # create inequalities of the form delta_i <= (q^r - 1)/(q^{gcd(i,r)} - 1)
            upper_bounds = [Integer((q**r - 1)/(q**(gcd(i, r)) - 1))] + [0]*(len(coeff_indices) + 1)
            upper_bounds[idx + 1] = -1

            inequalities.extend((lower_bounds, upper_bounds))

        equation.append(1 - q**r)

        # Create the polyhedron defined by the equation and the inequalities.
        polyhedron = Polyhedron(ieqs=inequalities, eqns=[equation])

        # Compute its integral points
        integral_points = polyhedron.integral_points()

        return [(tuple(coeff_indices), tuple(p)) for p in integral_points if gcd(p) == 1]

    def basic_j_invariants(self):
        r"""
        Return a dictionnary whose keys are the basic `j`-invariants parameters
        and values are the associated `j`-invariant.

        See the method :meth:`j_invariant` for the definition of the basic
        `j`-invariants.

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi.basic_j_invariants()
            {((1,), (26, 1)): z12^10 + 4*z12^9 + 3*z12^8 + 2*z12^7 + 3*z12^6 + z12^5 + z12^3 + 4*z12^2 + z12 + 2}

        ::

            sage: A = GF(5)['T']
            sage: K.<T> = Frac(A)
            sage: phi = DrinfeldModule(A, [T, T + 2, T+1, 1])
            sage: J_phi = phi.basic_j_invariants(); J_phi
            {((1, 2), (0, 31, 6)): T^31 + T^30 + T^26 + T^25 + T^6 + T^5 + T + 1,
             ((1, 2), (1, 5, 1)): T^6 + 2*T^5 + T + 2,
             ((1, 2), (7, 4, 1)): T^11 + 3*T^10 + T^9 + 4*T^8 + T^7 + 2*T^6 + 2*T^4 + 3*T^3 + 2*T^2 + 3,
             ((1, 2), (8, 9, 2)): T^17 + 2*T^15 + T^14 + 4*T^13 + 4*T^11 + 4*T^10 + 3*T^9 + 2*T^8 + 3*T^7 + 2*T^6 + 3*T^5 + 2*T^4 + 3*T^3 + 4*T^2 + 3*T + 1,
             ((1, 2), (9, 14, 3)): T^23 + 2*T^22 + 2*T^21 + T^19 + 4*T^18 + T^17 + 4*T^16 + T^15 + 4*T^14 + 2*T^12 + 4*T^11 + 4*T^10 + 2*T^8 + 4*T^7 + 4*T^6 + 2*T^4 + T^2 + 2*T + 2,
             ((1, 2), (10, 19, 4)): T^29 + 4*T^28 + T^27 + 4*T^26 + T^25 + 2*T^24 + 3*T^23 + 2*T^22 + 3*T^21 + 2*T^20 + 4*T^19 + T^18 + 4*T^17 + T^16 + 4*T^15 + T^9 + 4*T^8 + T^7 + 4*T^6 + T^5 + 4*T^4 + T^3 + 4*T^2 + T + 4,
             ...
             ((1, 2), (31, 31, 7)): T^62 + 3*T^61 + 2*T^60 + 3*T^57 + 4*T^56 + T^55 + 2*T^52 + T^51 + 4*T^50 + 3*T^37 + 4*T^36 + T^35 + 4*T^32 + 2*T^31 + 3*T^30 + T^27 + 3*T^26 + 2*T^25 + 2*T^12 + T^11 + 4*T^10 + T^7 + 3*T^6 + 2*T^5 + 4*T^2 + 2*T + 3}
            sage: J_phi[((1, 2), (7, 4, 1))]
            T^11 + 3*T^10 + T^9 + 4*T^8 + T^7 + 2*T^6 + 2*T^4 + 3*T^3 + 2*T^2 + 3
        """
        return {p: self.j_invariant(p, check=False) for p in self.basic_j_invariant_parameters()}

    def coefficient(self, n):
        r"""
        Return the `n`-th coefficient of the generator.

        INPUT:

        - ``n`` -- a nonnegative integer

        OUTPUT: an element in the base codomain

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi.coefficient(0)
            2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi.coefficient(0) == p_root
            True
            sage: phi.coefficient(1)
            z12^3
            sage: phi.coefficient(2)
            z12^5
            sage: phi.coefficient(5)
            Traceback (most recent call last):
            ...
            ValueError: input must be >= 0 and <= rank
        """
        if not isinstance(n, Integer) and not isinstance(n, int):
            raise TypeError('input must be an integer')
        if not 0 <= n <= self.rank():
            raise ValueError('input must be >= 0 and <= rank')
        return self.coefficients(sparse=False)[n]

    def coefficients(self, sparse=True):
        r"""
        Return the coefficients of the generator, as a list.

        If the flag ``sparse`` is ``True`` (default), only return the
        nonzero coefficients; otherwise, return all of them.

        INPUT:

        - ``sparse`` -- a boolean

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi.coefficients()
            [2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12,
             z12^3,
             z12^5]

        Careful, the method only returns the nonzero coefficients,
        unless otherwise specified::

            sage: rho = DrinfeldModule(A, [p_root, 0, 0, 0, 1])
            sage: rho.coefficients()
            [2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12,
             1]
            sage: rho.coefficients(sparse=False)
            [2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12,
             0,
             0,
             0,
             1]
        """
        return self._gen.coefficients(sparse=sparse)

    def gen(self):
        r"""
        Return the generator of the Drinfeld module.

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi.gen() == phi(T)
            True
        """
        return self._gen

    def height(self):
        r"""
        Return the height of the Drinfeld module if the function field
        characteristic is a prime ideal; raise ValueError otherwise.

        The height of a Drinfeld module is defined when the function
        field characteristic is a prime ideal. In our case, this ideal
        is even generated by a monic polynomial `\mathfrak{p}` in the
        function field. Write `\phi_\mathfrak{p} = a_s \tau^s + \dots +
        \tau^{r*\deg(\mathfrak{p})}`. The height of the Drinfeld module
        is the well-defined positive integer `h =
        \frac{s}{\deg(\mathfrak{p})}`.

        .. NOTE::

            See [Gos1998]_, Definition 4.5.8 for the general definition.

        A rank two Drinfeld module is supersingular if and only if its
        height equals its rank.

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi.height() == 1
            True
            sage: phi.is_ordinary()
            True

        ::

            sage: B.<Y> = Fq[]
            sage: L = Frac(B)
            sage: phi = DrinfeldModule(A, [L(2), L(1)])
            sage: phi.height()
            Traceback (most recent call last):
            ...
            NotImplementedError: height not implemented in this case

        ::

            sage: Fq = GF(343)
            sage: A.<T> = Fq[]
            sage: K.<z6> = Fq.extension(2)
            sage: phi = DrinfeldModule(A, [1, 0, z6])
            sage: phi.height()
            2
            sage: phi.is_supersingular()
            True

        """
        try:
            if self.characteristic().is_zero():
                raise ValueError('height is defined for prime ' \
                                 'function field characteristic')
            else:
                p = self.characteristic()
                return Integer(self(p).valuation() // p.degree())
        except NotImplementedError:
            raise NotImplementedError('height not implemented in this case')

    def is_finite(self):
        r"""
        Return ``True`` if this Drinfeld module is finite,
        ``False`` otherwise.

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi.is_finite()
            True
            sage: B.<Y> = Fq[]
            sage: L = Frac(B)
            sage: psi = DrinfeldModule(A, [L(2), L(1)])
            sage: psi.is_finite()
            False
        """
        from sage.rings.function_field.drinfeld_modules.finite_drinfeld_module import FiniteDrinfeldModule
        return isinstance(self, FiniteDrinfeldModule)

    def is_isomorphic(self, psi):
        r"""
        Return ``True``  whether ``self`` is isomorphic to the Drinfeld module
        `\psi`.

        EXAMPLES::

            sage: A = GF(5)['T']
            sage: K.<T> = Frac(A)
            sage: c = T^4 + 3*T^2 + T
            sage: phi = DrinfeldModule(A, [T, T^3, T^9, T])
            sage: psi = DrinfeldModule(A, [T, c^4*T^3, c^(24)*T^9, c^(124)*T])
            sage: phi.is_isomorphic(psi)
            True
            sage: phi0 = DrinfeldModule(A, [T, 1, 1, 1])
            sage: phi.is_isomorphic(phi0)
            False

        ::

            sage: phi = DrinfeldModule(A, [T, 1, 0, 1, 0, 0, 0, T^2, 1, 1])
            sage: phi.is_isomorphic(phi)
            True
            sage: psi = DrinfeldModule(A, [T, 1, 0, 1, 0, T, 0, T^2, 1, 1])
            sage: phi.is_isomorphic(psi)
            False
        """
        # trivial checks:
        if self._gen == psi._gen:
            return True
        if self._gen.degree() != psi._gen.degree():
            return False
        if self._gen.degree() == 1:
            return True
        # check if self and psi are patterned alike:
        if not all(bool(g_self) == bool(g_psi) for g_self, g_psi in\
            zip(self._gen.coefficients(sparse=False), psi._gen.coefficients(sparse=False))):
            return False
        # check that all the nonzero basic j-invariants agree
        isom = True
        for p in self.basic_j_invariant_parameters(nonzero=True):
            if self.j_invariant(p, check=False) != psi.j_invariant(p, check=False):
                isom = False
                break
        return isom

    def j_invariant(self, parameter=None, check=True):
        r"""
        Return the `j`-invariant of the Drinfeld `\mathbb{F}_q[T]`-module for
        the given parameter.

        Suppose that `\phi_T = g_0 + g_1\tau + \cdots + g_r \tau^r` with
        `g_r \neq 0`. Then the
        `((k_1, \ldots, k_n), (d_1, \ldots, d_n, d_r)`-`j`*-invariant* of `\phi`
        is defined by

        .. MATH::

            j_{k_1, \ldots, k_n}^{d_1, \ldots, d_n, d_r}(\phi) := \frac{1}{g_r^{d_q}}\prod_{i = 1}^n g_{k_i}^{d_i}

        where `1\leq k_1 < k_2 < \ldots < k_n \leq r - 1` and the integers `d_i`
        satisfies the *weight-0 condition*:

        .. MATH::

            d_1 (q^{k_1} - 1) + d_2 (q^{k_2} - 1) + ... + d_{n} (q^{k_n} - 1) = d_r (q^r - 1).

        Furthermore, if `\gcd(d_1,\ldots, d_n, d_r) = 1` and

        .. MATH::

            0 \leq d_i \leq (q^r - 1)/(q^{\gcd(i, r)} - 1), \quad 1 \leq i \leq n,

        then the `j`-invariant is called *basic*. See the method
        :meth:`basic_j_invariant_parameters` for computing the list of all basic
        `j`-invariant parameters.

        INPUT:

        - ``parameter`` (integer or tuple, default: None) -- this parameter is
          either a tuple of two tuples or an integer between 1 and `r-1` (`r` is
          the rank).

          - If ``parameter`` is a tuple of two tuples, then it must be of the
            form `((k_1, k_2, \ldots, k_n), (d_1, d_2, \ldots, d_n, d_r))` where
            the `k_i` and `d_i` are integers satisfying the weight-0 condition
            described above. In this case the method returns the associated
            `j`-invariant;

          - If ``parameter`` is an integer `k` then the method returns
            the ``j``-invariant associated to the parameter `((k,), (d_k, d_r))`;

          - If ``parameter`` is ``None`` and the rank of the Drinfeld module is
            2, then the method returns its usual `j`-invariant, that is the
            `j`-invariant for the parameter `((1,), (q+1, 1))`.

        - ``check`` (bool, default: ``True``) -- if this flag is set to
          ``False`` then the code will not check if the given parameter is valid
          and satisfy the weight-0 condition.

        OUTPUT: the `j`-invariant of ``self`` for the given parameter.

        REFERENCE:

        The notion of basic `j`-invariant was introduced by Potemine in
        [Pot1998]_.

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi.j_invariant()
            z12^10 + 4*z12^9 + 3*z12^8 + 2*z12^7 + 3*z12^6 + z12^5 + z12^3 + 4*z12^2 + z12 + 2
            sage: psi = DrinfeldModule(A, [p_root, 1, 1])
            sage: psi.j_invariant()
            1
            sage: rho = DrinfeldModule(A, [p_root, 0, 1])
            sage: rho.j_invariant()
            0

        ::

            sage: A = GF(5)['T']
            sage: K.<T> = Frac(A)
            sage: phi = DrinfeldModule(A, [T, T^2, 1, T + 1, T^3])
            sage: phi.j_invariant(1)
            T^309
            sage: phi.j_invariant(2)
            1/T^3
            sage: phi.j_invariant(3)
            (T^156 + T^155 + T^151 + T^150 + T^131 + T^130 + T^126 + T^125 + T^31 + T^30 + T^26 + T^25 + T^6 + T^5 + T + 1)/T^93

        ::

            sage: Fq.<a> = GF(7)
            sage: A.<T> = Fq[]
            sage: phi = DrinfeldModule(A, [a, a^2 + a, 0, 3*a, a^2+1])
            sage: J = phi.j_invariant(((1, 3), (267, 269, 39))); J
            5
            sage: J == (phi.coefficient(1)**267)*(phi.coefficient(3)**269)/(phi.coefficient(4)**39)
            True
            sage: phi.j_invariant(((3,), (400, 57)))
            4
            sage: phi.j_invariant(((3,), (400, 57))) == phi.j_invariant(3)
            True

        The list of all basic `j`-invariant parameters can be retrieved using
        the method :meth:`basic_j_invariant_parameters`::

            sage: A = GF(3)['T']
            sage: K.<T> = Frac(A)
            sage: phi = DrinfeldModule(A, [T, T^2 + T + 1, 0, T^4 + 1, T - 1])
            sage: param = phi.basic_j_invariant_parameters(nonzero=True)
            sage: phi.j_invariant(param[0])
            T^13 + 2*T^12 + T + 2
            sage: phi.j_invariant(param[1])
            T^35 + 2*T^31 + T^27 + 2*T^8 + T^4 + 2

        TESTS::

            sage: A = GF(5)['T']
            sage: K.<T> = Frac(A)
            sage: phi = DrinfeldModule(A, [T, T^2, 1, T + 1, T^3])
            sage: phi.j_invariant()
            Traceback (most recent call last):
            ...
            TypeError: input 'parameter' must be different from NoneType if the rank is greater than 2
            sage: phi.j_invariant(-1)
            Traceback (most recent call last):
            ...
            ValueError: input 'parameter' must be >= 1 or < the rank (=4)
            sage: phi.j_invariant('x')
            Traceback (most recent call last):
            ...
            TypeError: input 'parameter' must be a tuple of length 2 or an integer
            sage: phi.j_invariant((1, 2, 3))
            Traceback (most recent call last):
            ...
            ValueError: input 'parameter' must be of length 2
            sage: phi.j_invariant(('x', (1, 2, 3)))
            Traceback (most recent call last):
            ...
            TypeError: first entry of input 'parameter' must be a tuple
            sage: phi.j_invariant(((1, 2), 'x'))
            Traceback (most recent call last):
            ...
            TypeError: second entry of input 'parameter' must be a tuple
            sage: phi.j_invariant(((1, 2, 3, 4, 5), (2, 1)))
            Traceback (most recent call last):
            ...
            ValueError: tuples of input 'parameters' are of incorrect length
            sage: phi.j_invariant(((1, 'x'), (2, 3, 8)))
            Traceback (most recent call last):
            ...
            TypeError: first tuple of input 'parameter' must contain only integers
            sage: phi.j_invariant(((1, 2), (2, 3, 'x')))
            Traceback (most recent call last):
            ...
            TypeError: second tuple of input 'parameter' must contain only integers
            sage: phi.j_invariant(((1, 2), (4, 3, 7)))
            Traceback (most recent call last):
            ...
            ValueError: input 'parameter' does not satisfy the weight-0 condition
            sage: phi.j_invariant(((1, 2), (4, 3, 7)), check=False)
            1/T^13
        """
        r = self._gen.degree()
        q = self._Fq.order()
        if parameter is None:
            if r != 2:
                raise TypeError("input 'parameter' must be different from "
                                 "NoneType if the rank is greater than 2")
            return self._gen[1]**(q+1)/self._gen[2]
        if isinstance(parameter, (int, Integer)):
            if parameter <= 0 or parameter >= r:
                raise ValueError("input 'parameter' must be >= 1 or < the "
                                 f"rank (={r})")
            dk = Integer((q**r - 1)/(q**gcd(parameter, r) - 1))
            dr = Integer((q**parameter - 1)/(q**gcd(parameter, r) - 1))
            return self._gen[parameter]**dk / self._gen[-1]**dr
        elif isinstance(parameter, tuple):
            if len(parameter) != 2:
                raise ValueError("input 'parameter' must be of length 2")
            if not isinstance(parameter[0], tuple):
                raise TypeError("first entry of input 'parameter' must be "
                                "a tuple")
            if not isinstance(parameter[1], tuple):
                raise TypeError("second entry of input 'parameter' must be "
                                "a tuple")
            if not len(parameter[0]) < r or not len(parameter[1]) == len(parameter[0]) + 1:
                raise ValueError("tuples of input 'parameters' are of incorrect length")
            if not all(isinstance(p, (int, Integer)) for p in parameter[0]):
                raise TypeError("first tuple of input 'parameter' must "
                                "contain only integers")
            if not all(isinstance(p, (int, Integer)) for p in parameter[1]):
                raise TypeError("second tuple of input 'parameter' must "
                                "contain only integers")
            if check:
                # check that the weight-0 condition is statisfied:
                # d_1 (q - 1) + d_2 (q^2 - 1) + ... + d_{r-1} (q^{r-1} - 1) = d_r (q^r - 1)
                right = parameter[1][-1]*(q**r - 1)
                left = sum(parameter[1][i]*(q**(parameter[0][i]) - 1) for i in
                        range(len(parameter[0])))
                if left != right:
                    raise ValueError("input 'parameter' does not satisfy the "
                                    "weight-0 condition")
        else:
            raise TypeError("input 'parameter' must be a tuple of length 2 or "
                            "an integer")
        num = prod(self._gen[k]**d for k, d in zip(parameter[0], parameter[1][:-1]))
        return num/(self._gen[-1]**parameter[1][-1])

    def morphism(self):
        r"""
        Return the morphism object that defines the Drinfeld module.

        OUTPUT: a ring morphism from the function ring to the Ore
        polynomial ring

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi.morphism()
            Ring morphism:
              From: Univariate Polynomial Ring in T over Finite Field in z2 of size 5^2
              To:   Ore Polynomial Ring in t over Finite Field in z12 of size 5^12 over its base twisted by Frob^2
              Defn: T |--> z12^5*t^2 + z12^3*t + 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: from sage.rings.morphism import RingHomomorphism
            sage: isinstance(phi.morphism(), RingHomomorphism)
            True

        Actually, the ``DrinfeldModule`` method :meth:`__call__` simply
        class the ``__call__`` method of this morphism::

            sage: phi.morphism()(T) == phi(T)
            True
            sage: a = A.random_element()
            sage: phi.morphism()(a) == phi(a)
            True

        And many methods of the Drinfeld module have a counterpart in
        the morphism object::

            sage: m = phi.morphism()
            sage: m.domain() is phi.function_ring()
            True
            sage: m.codomain() is phi.ore_polring()
            True
            sage: m.im_gens()
            [z12^5*t^2 + z12^3*t + 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12]
            sage: phi(T) == m.im_gens()[0]
            True
        """
        return self._morphism

    def rank(self):
        r"""
        Return the rank of the Drinfeld module.

        In our case, the rank is the degree of the generator.

        OUTPUT: an integer

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: phi.rank()
            2
            sage: psi = DrinfeldModule(A, [p_root, 2])
            sage: psi.rank()
            1
            sage: rho = DrinfeldModule(A, [p_root, 0, 0, 0, 1])
            sage: rho.rank()
            4
        """
        return self._gen.degree()

    def velu(self, isog):
        r"""
        Return a new Drinfeld module such that input is an
        isogeny to this module with domain ``self``; if no such isogeny
        exists, raise an exception.

        INPUT:

        - ``isog`` -- the Ore polynomial that defines the isogeny

        OUTPUT: a Drinfeld module

        ALGORITHM:

            The input defines an isogeny if only if:

            1. The degree of the characteristic divides the height of
            the input. (The height of an Ore polynomial `P(\tau)` is the
            maximum `n` such that `\tau^n` right-divides `P(\tau)`.)

            2. The input right-divides the generator, which can
            be tested with Euclidean division.

            We test if the input is an isogeny, and, if it is, we
            return the quotient of the Euclidean division.

            Height and Euclidean division of Ore polynomials are
            implemented as methods of class
            :class:`sage.rings.polynomial.ore_polynomial_element.OrePolynomial`.

            Another possible algorithm is to recursively solve a system,
            see :arxiv:`2203.06970`, Eq. 1.1.

        EXAMPLES::

            sage: Fq = GF(25)
            sage: A.<T> = Fq[]
            sage: K.<z12> = Fq.extension(6)
            sage: p_root = 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: phi = DrinfeldModule(A, [p_root, z12^3, z12^5])
            sage: t = phi.ore_polring().gen()
            sage: isog = t + 2*z12^11 + 4*z12^9 + 2*z12^8 + 2*z12^6 + 3*z12^5 + z12^4 + 2*z12^3 + 4*z12^2 + 4*z12 + 4
            sage: psi = phi.velu(isog)
            sage: psi
            Drinfeld module defined by T |--> (z12^11 + 3*z12^10 + z12^9 + z12^7 + z12^5 + 4*z12^4 + 4*z12^3 + z12^2 + 1)*t^2 + (2*z12^11 + 4*z12^10 + 2*z12^8 + z12^6 + 3*z12^5 + z12^4 + 2*z12^3 + z12^2 + z12 + 4)*t + 2*z12^11 + 2*z12^10 + z12^9 + 3*z12^8 + z12^7 + 2*z12^5 + 2*z12^4 + 3*z12^3 + z12^2 + 2*z12
            sage: isog in Hom(phi, psi)
            True

        This method works for endomorphisms as well::

            sage: phi.velu(phi(T)) is phi
            True
            sage: phi.velu(t^6) is phi
            True

        The following inputs do not define isogenies, and the method
        returns ``None``::

            sage: phi.velu(0)
            Traceback (most recent call last):
            ...
            ValueError: the input does not define an isogeny
            sage: phi.velu(t)
            Traceback (most recent call last):
            ...
            ValueError: the input does not define an isogeny
            sage: phi.velu(t^3 + t + 2)
            Traceback (most recent call last):
            ...
            ValueError: the input does not define an isogeny
        """
        if isog not in self.ore_polring():
            raise TypeError('input must be an Ore polynomial')
        e = ValueError('the input does not define an isogeny')
        if isog == 0:
            raise e
        quo, rem = (isog * self.gen()).right_quo_rem(isog)
        char_deg = self.characteristic().degree()
        if not char_deg.divides(isog.valuation()) \
                or rem != 0:
            raise e
        else:
            return self.category().object(quo)
