from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Job:
    href: Optional[str] = None
    company_name: Optional[str] = None
    job_name: Optional[str] = None
    job_area: Optional[str] = None
    company_tag: Optional[str] = None # e.g., "tag1·tag2·tag3"
    salary: Optional[str] = None
    recruiter: Optional[str] = None
    site_name: Optional[str] = None
    applied_status: str = "Not Applied"
    details_extracted: bool = False

    def __str__(self):
        return f"Job(name='{self.job_name}', company='{self.company_name}', area='{self.job_area}', salary='{self.salary}')"
