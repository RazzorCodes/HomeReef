from concurrent.futures import ThreadPoolExecutor, as_completed

import schedule
from governors.activity import Activity
from governors.scan_activity import ScanActivity
from dataclasses import field

class Governor:
    pass


class ActivityGovernor(Governor):
    _activities: list[Activity] = field(default_factory=list)

    def __init__(self, activities: list[Activity]):
        self._activities = activities

    def schedule_activities(self):
        for activity in self._activities:
            