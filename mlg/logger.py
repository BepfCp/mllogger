import atexit
import json
import os
import sys
from datetime import datetime
from os.path import join
from typing import Any, Dict, List

from loguru import _defaults
from loguru._logger import Core as _Core
from loguru._logger import Logger as _Logger
from tensorboardX import SummaryWriter


class IntegratedLogger(_Logger, SummaryWriter):
    def __init__(
        self, record_param: List[str] = None, log_root: str = "logs", args: Dict = None
    ):
        """
        :param record_param: Used for name the experiment results dir
        :param log_root: The root path for all logs
        """
        # init loguru, copied from loguru.__init__.py
        _Logger.__init__(
            self,
            core=_Core(),
            exception=None,
            depth=0,
            record=False,
            lazy=False,
            colors=False,
            raw=False,
            capture=True,
            patcher=None,
            extra={},
        )

        if _defaults.LOGURU_AUTOINIT and sys.stderr:
            self.add(sys.stderr)

        atexit.register(self.remove)

        # Hyperparam
        self.log_root = log_root
        self.args = args
        self.record_param_dict = self._parse_record_param(record_param)

        # Do not change the following orders.
        self._create_print_logger()
        self._create_ckpt_result_dir()
        self._dump_args()

        # Init SummaryWriter
        SummaryWriter.__init__(self, logdir=self.exp_dir)

    def _create_print_logger(self):
        self.exp_dir = join(self.log_root, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        if self.record_param_dict is not None:
            for key, value in self.record_param_dict.items():
                self.exp_dir = self.exp_dir + f"&{key}={value}"
        self.add(join(self.exp_dir, "log.log"), format="{time} -- {level} -- {message}")

    def _create_ckpt_result_dir(self):
        self.ckpt_dir = join(self.exp_dir, "checkpoint")
        os.makedirs(self.ckpt_dir)  # checkpoint, for model, data, etc.

        self.resutl_dir = join(self.exp_dir, "result")
        os.makedirs(self.resutl_dir)  # result, for some intermediate result

    def _parse_record_param(self, record_param: List[str]) -> Dict[str, Any]:
        if self.args is None or record_param is None:
            return None
        else:
            record_param_dict = dict()
            for param in record_param:
                param = param.split(".")
                value = self.args
                for p in param:
                    value = value[p]
                record_param_dict["-".join(param)] = value
            return record_param_dict

    def _dump_args(self):
        if self.args is None:
            return
        else:
            with open(join(self.exp_dir, "parameter.json"), "w") as f:
                jd = json.dumps(self.args, indent=4)
                print(jd, file=f)
