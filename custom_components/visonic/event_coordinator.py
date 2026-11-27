"""Coordinator for deduplicating and debouncing panel state/event messages."""

from __future__ import annotations

import asyncio

from .pyconst import AlCondition, PE_EVENT, PE_NAME, PE_PARTITION, PE_TIME


class PanelEventCoordinator:
    """Manage A5, B0.24 and A7 panel state and event data debouncing."""

    def __init__(self, loop, callbackSender, ispm: bool = False, logstate_debug=None):
        self.logstate_debug = self._dummy if logstate_debug is None else logstate_debug
        self.callbackSender = self._dummy if callbackSender is None else callbackSender
        self.logstate_debug("[EC] Starting")
        self.loop = loop
        self.isPowerMaster = ispm
        self._init_vars()

    def _init_vars(self):
        self.EventTime = 0
        self.EventName = 0
        self.EventAction = -100
        self.EventPartition = None
        self._event_timer_task = None
        self.timerAlreadySent = True

    def close(self):
        try:
            if self._event_timer_task is not None:
                self._event_timer_task.cancel()
            self._init_vars()
        except Exception as ex:
            self.logstate_debug("[PanelEventCoordinator]     Close Caused an exception")
            self.logstate_debug(f"             {ex}")

    def _dummy(self, msg, *args, **kwargs):
        pass

    def _sendData(self):
        if self.EventAction >= 0:
            d = self._convert()
            self.logstate_debug(f"[EC] sending panel update {self.EventName=} {self.EventAction=} as data {d}")
            self.callbackSender(AlCondition.PANEL_UPDATE, d)
        else:
            self.logstate_debug("[EC] _sendData wont send blank data")

    def _convert(self) -> dict:
        from . import pmLogEvent_t, pmLogPowerMasterUser_t, pmLogPowerMaxUser_t

        d = {}
        d[PE_NAME] = "Unknown"
        if self.isPowerMaster:
            d[PE_NAME] = pmLogPowerMasterUser_t[self.EventName] or "Unknown"
        else:
            d[PE_NAME] = pmLogPowerMaxUser_t[int(self.EventName & 0x7F)] or "Unknown"

        d[PE_EVENT] = "Unknown"
        if 0 <= self.EventAction < len(pmLogEvent_t):
            if len(pmLogEvent_t[self.EventAction]) > 0:
                d[PE_EVENT] = pmLogEvent_t[self.EventAction]

        d[PE_TIME] = self.EventTime
        if self.EventPartition is not None:
            d[PE_PARTITION] = self.EventPartition
        return d

    async def _event_timer(self):
        self.timerAlreadySent = False
        await asyncio.sleep(0.4)
        self._sendData()
        self.timerAlreadySent = True

    def _send_and_replace(self, data: dict):
        if self._event_timer_task is not None:
            try:
                self._event_timer_task.cancel()
            except Exception as ex:
                self.logstate_debug("[_send_and_replace]     Caused an exception")
                self.logstate_debug(f"             {ex}")
        if not self.timerAlreadySent:
            self._sendData()
        self.EventName = data[PE_NAME]
        self.EventAction = data[PE_EVENT]
        self.EventTime = data[PE_TIME]
        self.EventPartition = data[PE_PARTITION] if PE_PARTITION in data else None
        converted = self._convert()
        part_str = converted[PE_PARTITION] if self.EventPartition is not None else "Not set as it is a panel"
        self.logstate_debug(
            f"[EC] _send_and_replace {data}     partition = {part_str}    "
            f"name = {converted[PE_NAME]}    event = {converted[PE_EVENT]}"
        )
        self._event_timer_task = self.loop.create_task(self._event_timer())

    def addEvent(self, pm, data: dict) -> bool:
        self.isPowerMaster = pm
        if data is not None:
            if self.EventAction != data[PE_EVENT]:
                self._send_and_replace(data)
                return True
            if self.EventName == data[PE_NAME]:
                return False
            if self.EventName != 0 and data[PE_NAME] == 0:
                self.logstate_debug(f"[EC] Panel event data {data} is the same Event but I already have a better name")
                return False
            if self.EventName == 0 and data[PE_NAME] != 0:
                self.logstate_debug(f"[EC] Replacing 'system' with {data[PE_NAME]} but keeping original time {self.EventTime}")
                self.EventName = data[PE_NAME]
            self._send_and_replace(data)
            return True
        return False
