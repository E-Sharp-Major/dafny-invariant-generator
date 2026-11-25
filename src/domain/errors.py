class DafnyInvariantError(Exception):
    """Base class for all errors raised deliberately by this application"""


class ConfigError(DafnyInvariantError):
    """Invalid or contradictory configuration (eg output path equals input path)"""


class InfrastructureError(DafnyInvariantError):
    """An external component (LM Studio, Dafny, filesystem) is unusable"""


class LLMUnavailableError(InfrastructureError):
    """The LLM server cannot be reached or returned an unusable response"""


class ModelNotFoundError(InfrastructureError):
    """The requested model id is not known to the LLM server"""


class DafnyNotFoundError(InfrastructureError):
    """The Dafny executable could not be found or started"""