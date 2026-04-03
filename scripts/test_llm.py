"""
Quick test script to verify LLM configuration works
"""

from core.llm_client import LLMClient
from core.logger import setup_logger

logger = setup_logger("LLMTest")


def main():
    logger.info("Testing LLM configuration...")

    try:
        # Initialize client (reads from .env)
        client = LLMClient()

        logger.info(f"✓ Provider: {client.provider}")
        logger.info(f"✓ Model: {client.model}")
        logger.info(f"✓ Temperature: {client.temperature}")
        logger.info(f"✓ Max tokens: {client.max_tokens}")

        # Test simple chat
        logger.info("\nSending test message to LLM...")

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Respond in one short sentence."
            },
            {
                "role": "user",
                "content": "Say 'LLM configuration is working correctly' in a friendly way."
            }
        ]

        response = client.chat(messages)

        logger.info(f"\n✓ LLM Response: {response.strip()}")
        logger.info("\n" + "=" * 60)
        logger.info("SUCCESS: LLM configuration is working correctly!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"\n✗ LLM Test Failed: {str(e)}")
        logger.error("\nTroubleshooting:")
        logger.error("1. Check your .env file exists")
        logger.error("2. Verify LLM_PROVIDER is set correctly")
        logger.error("3. For cloud providers, ensure API key is valid")
        logger.error("4. For Ollama, ensure it's running: ollama serve")
        logger.error("\nSee LLM_CONFIGURATION.md for detailed setup instructions")
        raise


if __name__ == "__main__":
    main()
