from typing import Dict
import sys
import types
import unittest
from io import StringIO
import multiprocessing as mp
import traceback


# ──────────────────────────────────────────────────────────────────────────────
def _worker(solution_code: str, tests_code: str, queue: mp.Queue):
    """
    Запускается в отдельном процессе. Кладёт в очередь подробные статусы.
    """
    try:
        runner = TestRunner()
        statuses = runner._run_inline(solution_code, tests_code)
        queue.put(statuses)
    except Exception:
        queue.put({
            '__worker_error__': 'error',
            '__traceback__': traceback.format_exc()
        })


class TestRunner:
    """
    Запускает unittest-тесты и возвращает словарь вида
    {test.id(): {"status": <passed/failed/error/skipped>, "message": <--->}}.
    При таймауте — {"__timeout__": "timeout"}.
    """

    _MAP = {'success': 'passed',
            'failure': 'failed',
            'error':   'error',
            'skipped': 'skipped'}

    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def _flatten(suite: unittest.TestSuite):
        """Рекурсивно разворачивает TestSuite → TestCase."""
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                yield from TestRunner._flatten(test)
            else:
                yield test

    # ──────────────────────────────────────────────────────────────────────
    def _run_inline(self, solution_code: str, tests_code: str) -> dict[str, dict]:
        """Запускает тесты внутри текущего процесса (без таймаута)."""
        # 1. динамически создаём модуль с решением
        sol_mod = types.ModuleType('solution')
        exec(compile(solution_code, '<solution>', 'exec'), sol_mod.__dict__)
        sys.modules['solution'] = sol_mod

        # 2. динамически создаём модуль с тестами
        tst_mod = types.ModuleType('solution_tests')
        exec(compile(tests_code, '<tests>', 'exec'), tst_mod.__dict__)

        # 3. строим suite и плоский список всех тестов
        suite = unittest.defaultTestLoader.loadTestsFromModule(tst_mod)
        all_tests = list(self._flatten(suite))

        # 4. запускаем
        buf = StringIO()
        result = unittest.TextTestRunner(stream=buf, verbosity=0).run(suite)

        # 5. словарь со статусами + пояснениями
        statuses: dict[str, dict] = {
            t.id(): {"status": self._MAP['success'], "message": ""}
            for t in all_tests
        }

        # 5-а. FAILED (assertion)
        for test, tb in result.failures:
            # последняя строка trace-а обычно содержит причину
            last_line = tb.strip().splitlines()[-1] if tb else ""
            statuses[test.id()] = {"status": self._MAP['failure'],
                                   "message": last_line}

        # 5-б. ERROR (исключение)
        for test, tb in result.errors:
            # оставим целиком: так проще искать место падения
            statuses[test.id()] = {"status": self._MAP['error'],
                                   "message": tb.strip()}

        # 5-в. SKIPPED
        for test, reason in getattr(result, 'skipped', []):
            statuses[test.id()] = {"status": self._MAP['skipped'],
                                   "message": reason}

        return statuses

    # ──────────────────────────────────────────────────────────────────────
    def run_tests(self,
                  solution_code: str,
                  tests_code: str,
                  timeout: float = 5.0) -> Dict[str, Dict[str, str]]:
        """
        Запускает _worker в отдельном процессе.
        Если превысили `timeout`, возвращает {"__timeout__": "timeout"}.
        """
        queue: mp.Queue = mp.Queue()
        proc = mp.Process(target=_worker, args=(solution_code, tests_code, queue))
        proc.start()
        proc.join(timeout)

        if proc.is_alive():              # таймаут!
            proc.terminate()
            proc.join()
            return {'__timeout__': {"status": "timeout"}}

        # дочерний процесс завершился раньше таймаута
        if not queue.empty():
            return queue.get()

        # должно быть крайне редко, но пусть будет
        return {'__error__': {"status": "no result returned from worker"}}
