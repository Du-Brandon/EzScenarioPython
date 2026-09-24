"""Constants matching ezSpec's built-in test tag vocabulary.

Adapted from ezSpec's EzSpecTag.java and LivingDoc.java into Python constants.
See NOTICE and docs/SOURCE_PROVENANCE.md for source and project attribution.
"""


class EzSpecTag:
    class Env:
        Dev = "Env.Development"
        Testing = "Env.Testing"
        Staging = "Env.Staging"
        Production = "Env.Production"

    class TestType:
        Unit = "TestType.Unit"
        Integration = "TestType.Integration"
        UseCase = "TestType.UseCase"
        EndToEnd = "TestType.EndToEnd"
        Sanity = "TestType.Sanity"
        AssertionFree = "TestType.AssertionFree"
        Trivial = "TestType.Trivial"
        Report = "TestType.Report"

    class CQRS:
        Command = "CQRS.Command"
        Query = "CQRS.Query"

    class DI:
        RAM = "DI.RAM"
        SpringBoot = "DI.SpringBoot"

    class Other:
        pass

    class Speed:
        Fast = "Speed.Fast"
        Slow = "Speed.Slow"

    class LivingDoc:
        EzSpec = "LivingDoc.EzSpec"


class LivingDoc:
    """Marker base class for living-documentation-aware objects."""
