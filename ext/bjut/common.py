#
# A Python script for reading GEM5 config and stat files.
#
# Copyright (C) Min Cai 2015
#

import os
import traceback
import collections
import json
from objectpath import *
from pyparsing import Word, Optional, ParseException, printables, nums, restOfLine


class Experiment:
    def __init__(self, dir, bench=None, l2_size=None, l2_assoc=None, l2_tags=None):
        self.bench = bench
        self.l2_size = l2_size
        self.l2_assoc = l2_assoc
        self.l2_tags = l2_tags

        self.dir = dir

        self.configs = self.read_configs()
        self.stats = self.read_stats()

    def read_configs(self):
        try:
            with open(self.config_json_file_name()) as config_json_file:
                config = json.load(config_json_file)
            return Tree(config)
        except:
            traceback.print_exc()
            return None

    def read_stats(self):
        stat_rule = Word(printables) + Word('nan.%' + nums) + Optional(restOfLine)
        section_num_to_use = 2

        stats = collections.OrderedDict()

        try:
            with open(self.stats_file_name()) as stats_file:
                i = 0
                for stat_line in stats_file:
                    if 'End Simulation Statistics' in stat_line:
                        i += 1
                    elif i == section_num_to_use:
                        try:
                            stat = stat_rule.parseString(stat_line)
                            key = stat[0]
                            value = stat[1]
                            stats[key] = value
                        except ParseException:
                            pass

            return stats
        except:
            traceback.print_exc()
            return None

    def config_json_file_name(self):
        return os.path.join(self.dir, 'config.json')

    def stats_file_name(self):
        return os.path.join(self.dir, 'stats.txt')

    def mcpat_in_xml_file_name(self):
        return os.path.join(self.dir, 'mcpat_in.xml')

    def mcpat_out_file_name(self):
        return os.path.join(self.dir, 'mcpat_out.txt')

    def num_cpus(self):
        return -1 if self.configs is None else self.configs.execute('len($.system.cpu)')

    def num_l2caches(self):
        return -1 if self.configs is None else self.configs.execute('len($.system.l2cache)')

    def numa(self):
        return False if self.configs is None else self.configs.execute('len($.system.numa_caches_upward)') > 0

    def cpu_id(self, i, l1=False):
        return '' if self.configs is None else self.configs.execute('$.system.' + ('switch_cpus' if not l1 else 'cpu') + '[' + str(i) + '].name')

    def l2_id(self, i=None):
        return '' if self.configs is None else ('l2' if i is None else self.configs.execute('$.system.l2cache[' + str(i) + '].name'))

    def sim_ticks(self):
        return -1 if self.stats is None else str(int(self.stats['sim_ticks']))

    def num_cycles(self):
        return -1 if self.stats is None else str(int(self.stats['system.' + self.cpu_id(0) + '.numCycles']))

    def l2_miss_rate(self):
        if self.stats is None:
            return -1

        miss_rates = []

        if self.numa():
            for i in range(self.num_l2caches()):
                miss_rates.append(float(self.stats['system.' + self.l2_id(i) + '.overall_miss_rate::total']))
        else:
            miss_rates.append(float(self.stats['system.' + self.l2_id() + '.overall_miss_rate::total']))

        return sum(miss_rates) / float(len(miss_rates))

    def l2_replacements(self):
        if self.stats is None:
            return -1

        replacements = []

        if self.numa():
            for i in range(self.num_l2caches()):
                replacements.append(int(self.stats['system.' + self.l2_id(i) + '.tags.replacements']))
        else:
            replacements.append(int(self.stats['system.' + self.l2_id() + '.tags.replacements']))

        return sum(replacements)

    @classmethod
    def dump_head_row(cls):
        pass

    def dump_row(self):
        pass
