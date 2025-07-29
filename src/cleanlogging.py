import logging
import os

# Suppress verbose ADK and Google API logs
logging.getLogger("google_adk.google.adk.models.google_llm").setLevel(logging.WARNING)
logging.getLogger("google_genai._api_client").setLevel(logging.WARNING)
logging.getLogger("google_genai.models").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_adk").setLevel(logging.WARNING)

# Keep only essential logs
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    force=True
)

# Create a clean logger for your agent steps
step_logger = logging.getLogger("AGENT_STEPS")
step_logger.setLevel(logging.INFO)

# Custom handler that only shows our key info
class CleanStepHandler(logging.StreamHandler):
    def emit(self, record):
        if record.name == "AGENT_STEPS":
            super().emit(record)

# Add our clean handler
clean_handler = CleanStepHandler()
clean_handler.setFormatter(logging.Formatter('🔄 %(message)s'))
step_logger.addHandler(clean_handler)
step_logger.propagate = False