from datetime import date, datetime
from typing import Dict, List
from http_client import HTTPClient
from dataclasses import dataclass, field

import xml.etree.ElementTree as ET
import re


@dataclass
class Stock:
    company_name: str
    cusip: str
    shares: int


@dataclass
class AccessionFiling:
    """Represents 13F filing.

    Args:
        formatted_accession_number (str): Access number formatted as this string XXXXXXX-XX-XXXX
        accession_number (str): Access number for file
        report_date (str): Date the file was reported
    """

    formatted_accession_number: str
    accession_number: str = field(init=False)
    report_date: date

    def __post_init__(self):
        self.accession_number = "".join(self.formatted_accession_number.split("-"))

    def __str__(self) -> str:
        return f"{self.report_date} -- {self.accession_number}"


@dataclass
class Corporation:
    cik_number: str
    accession_filings: List[AccessionFiling]


class Edgar:
    data_sec_client = HTTPClient(
        headers_dict={
            "User-Agent": "Omnia LLC omniallc2018@gmail.com",
            "Accept-Encoding": "gzip, deflate, br",
            "Host": "data.sec.gov",
        }
    )

    sec_client = HTTPClient(
        headers_dict={
            "User-Agent": "Omnia LLC omniallc2018@gmail.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
        }
    )

    @staticmethod
    def build_submissions_url(cik_num: str) -> str:
        return f"https://data.sec.gov/submissions/CIK{cik_num}.json"

    @staticmethod
    def build_investment_data_url(
        cik_num: str, access_num: str, formatted_access_num: str
    ) -> str:
        """Builds url that will be used to access investment data

        Args:
            cik_num (str): CIK number without first 0s
            access_num (str): Access number for file
            formatted_access_num (str): Access number formatted as this string XXXXXXX-XX-XXXX

        Returns:
            str: Returns url to access investment data
        """
        return f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{access_num}/{formatted_access_num}.txt"

    @staticmethod
    def retrieve_submissions(cik_num: str) -> Corporation:
        submissions_client = Edgar.data_sec_client

        submissions_url = Edgar.build_submissions_url(cik_num)
        data = submissions_client.get(submissions_url)
        json_data = data.json()

        parsed_cik_num = json_data["cik"]
        recent_filings = json_data["filings"]["recent"]

        accession_filings: List[AccessionFiling] = []

        for i, form_type in enumerate(recent_filings["form"]):
            if form_type == "13F-HR":
                accession_filings.append(
                    AccessionFiling(
                        formatted_accession_number=recent_filings["accessionNumber"][i],
                        report_date=datetime.strptime(
                            recent_filings["reportDate"][i], "%Y-%m-%d"
                        ),
                    )
                )

        return Corporation(
            cik_number=parsed_cik_num, accession_filings=accession_filings
        )

    @staticmethod
    def _retrieve_investment_data_for_accession_filing(
        cik_num: str, accession_filing: AccessionFiling
    ) -> List[Stock]:
        investment_data_url = Edgar.build_investment_data_url(
            cik_num=cik_num,
            access_num=accession_filing.accession_number,
            formatted_access_num=accession_filing.formatted_accession_number,
        )

        investment_client = Edgar.sec_client
        data = investment_client.get(investment_data_url)
        xml_str = re.search(
            "<informationTable[\s\S]*</informationTable>", data.text
        ).group(0)
        root_xml = ET.fromstring(xml_str)

        stocks: List[Stock] = []

        for infoTable in root_xml:
            stocks.append(
                Stock(
                    company_name=infoTable[0].text,
                    cusip=infoTable[2].text,
                    shares=int(infoTable[4][0].text),
                )
            )

        return stocks

    @staticmethod
    def retrieve_investment_data(cik_num: str, start=0, size=10) -> Dict[datetime, List[Stock]]:
        """Find investement data for provided cik number.

        Args:
            cik_num (str): SEC representation for entity
            start (int, optional): Find investment data starting from nth most recent filing. Defaults to 0 (most recent filling).
            size (int, optional): Continue finding data until size number of filings. Defaults to 10.

        Returns:
            Dict[datetime, List[Stock]]: Report filing date mapped to list of stocks at that date owned by this company.
        """

        corporation = Edgar.retrieve_submissions(cik_num=cik_num)
        return {
            accession_filing.report_date: Edgar._retrieve_investment_data_for_accession_filing(
                corporation.cik_number, accession_filing
            )
            for accession_filing in corporation.accession_filings[start:start+size]
        }
