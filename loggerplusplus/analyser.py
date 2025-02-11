# ====== Code Summary ======
# This script defines a `LogAnalyser` class that reads execution logs from a specified file,
# extracts function execution times using regular expressions, and plots them using Matplotlib.
# The script supports filtering execution times for specific function names and reports
# average execution times.

# ====== Imports ======
# Standard library imports
import re

# Third-party library imports
import matplotlib.pyplot as plt
import numpy as np


class LogAnalyser:
    """
    A class to analyze execution times of functions from a log file.

    Attributes:
        log_file_path (str): Path to the log file containing execution records.
    """

    def __init__(self, log_file_path: str):
        """
        Initializes the LogAnalyser with the given log file path.

        Args:
            log_file_path (str): Path to the log file.
        """
        self.log_file_path = log_file_path

    def analyse_time_tracker(
        self,
        func_names: str | list[str] | None = None,
        identifier: str | list[str] | None = None,
        min_execution_time_ms: float = 0.0,
        max_execution_time_ms: float = np.inf,
        is_sort_by_avg_time: bool = True,
        nb_max_funcs: int = np.iinfo(np.int32).max,
        is_sort_order_descending: bool = True,
    ):
        """
        Analyzes execution times for specified functions and generates a plot.

        Args:
            func_names (str | list[str] | None, optional): Function name(s) to filter.
            - If a string is provided, only that function is analyzed.
            - If a list of strings is provided, only those functions are analyzed.
            - If None, all functions are analyzed.
            identifier (str | list[str] | None, optional): Identifier(s) to filter log entries.
            - If a string is provided, only log entries with that identifier are analyzed.
            - If a list of strings is provided, only log entries with those identifiers are analyzed.
            - If None, all log entries are analyzed.
            min_execution_time_ms (float, optional): Minimum execution time in milliseconds to include in the analysis. Defaults to 0.0.
            max_execution_time_ms (float, optional): Maximum execution time in milliseconds to include in the analysis. Defaults to np.inf.
            sort_by_avg_time (bool, optional): If True, sort functions by average execution time. Defaults to True.
            nb_max_funcs (int, optional): Maximum number of functions to display in the plot, ignored if sort_by_avg_time is False. Defaults to np.iinfo(np.int32).max.
            order_by_max_execution_time (bool, optional): If True, order functions by maximum execution time, ignored if sort_by_avg_time is False. Defaults to True.
        """
        if isinstance(func_names, str):
            func_names = [func_names]
        elif func_names is None:
            func_names = [".*"]  # Match all functions

        if isinstance(identifier, str):
            identifier = [identifier]

        # Regular expression pattern to capture function execution times
        pattern = r"\[\s*([^\s\]]+)\s*\]\s+\[[\w.]+:[\d]+\]\s+\w+\s+\|\s+\[[\w.]+\]\s+(\w+)\(\)\s+executed\s+in\s+([\d.]+)s"

        times = {}

        # Open and read the log file
        with open(self.log_file_path, "r") as log_file:
            log_lines = log_file.readlines()

        # Extract execution times for each matching function
        for line in log_lines:
            match = re.search(pattern, line)
            if match:
                if identifier is None or match.group(1) in identifier:
                    function_name, execution_time = match.group(2), match.group(3)
                    if any(re.fullmatch(fn, function_name) for fn in func_names):
                        if (
                            min_execution_time_ms
                            <= float(execution_time) * 1000
                            <= max_execution_time_ms
                        ):
                            if function_name not in times:
                                times[function_name] = [float(execution_time)]
                            else:
                                times[function_name].append(float(execution_time))

        if not times:
            print("No matching execution times found in the log file.")
            return

        # Plot the execution times
        plt.figure(figsize=(10, 6))

        times_ms = list(map(lambda x: [t * 1000 for t in x], times.values()))
        average_times = [sum(t) / len(t) for t in times_ms]
        func_names = list(times.keys())

        # Sort by average_times while preserving index pairing
        if is_sort_by_avg_time:
            sorted_indices = sorted(
                range(len(average_times)),
                key=lambda i: average_times[i],
                reverse=is_sort_order_descending,
            )[:nb_max_funcs]
            func_names = [func_names[i] for i in sorted_indices]
            times_ms = [times_ms[i] for i in sorted_indices]
            average_times = [average_times[i] for i in sorted_indices]

        for i in range(len(func_names)):
            plt.plot(
                times_ms[i],
                label=f"{func_names[i]} (Avg: {average_times[i]:.6f} ms)",
                marker="o",
            )

        # Configure plot labels and title
        plt.xlabel("Execution Count")
        plt.ylabel("Time (ms)")
        plt.title("Function Execution Times")
        plt.legend()
        plt.grid(True)
        plt.show()

    def analyse_func_occurences(
        self,
        occurrence_threshold: int = 1,
        nb_func: int = -1,
        top_occ: bool = True,
        identifier: str | list[str] | None = None,
    ):
        """
        Analyzes the number of occurrences of each function in the log file and generates a bar plot.

        Args:
            occurrence_threshold (int, optional): Minimum number of occurrences for a function to be included in the analysis. Defaults to 1.
            nb_func (int, optional): Number of top functions to display based on occurrences. Defaults to -1 (display all).
            top_occ (bool, optional): If True, display functions with the highest occurrences first. If False, display functions with the lowest occurrences first. Defaults to True.
            identifier (str | list[str] | None, optional): Identifier(s) to filter log entries.
            - If a string is provided, only log entries with that identifier are analyzed.
            - If a list of strings is provided, only log entries with those identifiers are analyzed.
            - If None, all log entries are analyzed.
        """

        if isinstance(identifier, str):
            identifier = [identifier]

        # Regular expression patterns to capture function names for both cases
        patterns = [
            r"\[\s*([^\s\]]+)\s*\]\s+\[[\w.]+:[\d]+\]\s+\w+\s+\|\s+\[([^\]]+)\]\s+(\w+)\(\)\s+called",
            r"\[\s*([^\s\]]+)\s*\]\s+\[[\w.]+:[\d]+\]\s+\w+\s+\|\s+\[([^\]]+)\]\s+(\w+)\(\)\s+executed\s+in\s+[\d.]+s",
        ]

        func_occurrences = {}

        with open(self.log_file_path, "r") as log_file:
            log_lines = log_file.readlines()
            for line in log_lines:
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        match_identifier = match.group(1)
                        module_name = match.group(2).strip()
                        function_name = match.group(3)
                        full_name = f"{module_name}.{function_name}"

                        if module_name != "decorators" and (
                            identifier is None or match_identifier in identifier
                        ):
                            if full_name not in func_occurrences:
                                func_occurrences[full_name] = 1
                            else:
                                func_occurrences[full_name] += 1
                        break

            if not func_occurrences:
                print("No matching functions found in the log file.")
                return

            func_occurrences_list = [
                (func_name, count)
                for func_name, count in func_occurrences.items()
                if count >= occurrence_threshold
            ]

            if nb_func != -1:
                func_occurrences_list = sorted(
                    func_occurrences_list, key=lambda x: x[1], reverse=top_occ
                )[:nb_func]

            if not func_occurrences_list:
                print("No functions found with the specified occurrence threshold.")

            else:
                func_names, counts = zip(*func_occurrences_list)
                plt.figure(figsize=(12, 8))
                plt.bar(func_names, counts, color="skyblue")
                plt.xlabel("Function Names")
                plt.ylabel("Occurrences")
                plt.title("Function Occurrences in Log File")
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                plt.show()
