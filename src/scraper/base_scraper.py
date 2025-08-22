from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """
    Abstract base class for scraper plugins.
    """
    @property
    @abstractmethod
    def ecommerce_name(self) -> str:
        """
        Returns the name of the e-commerce platform.
        """
        pass

    @abstractmethod
    def scrape(self, query: str) -> list[dict]:
        """
        Scrapes the e-commerce platform for a given query.

        Args:
            query: The search query.

        Returns:
            A list of dictionaries, where each dictionary represents a scraped item.
        """
        pass
