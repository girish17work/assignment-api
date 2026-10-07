import unittest
from runner import execute_python_code


class ExecutionTests(unittest.TestCase):
    def test_exact_success(self):
        self.assertEqual(execute_python_code('print(5 + 10)'), {"success": True, "output": "15\n"})

    def test_runtime_line(self):
        result = execute_python_code('x = 10\ny = 0\nresult = x / y')
        self.assertFalse(result["success"])
        self.assertIn('File "<student>", line 3', result["output"])
        self.assertIn('ZeroDivisionError', result["output"])

    def test_syntax_line(self):
        result = execute_python_code('x = 10\nif True print(x)')
        self.assertFalse(result["success"])
        self.assertIn('File "<student>", line 2', result["output"])
        self.assertIn('SyntaxError', result["output"])

    def test_preserves_output_before_error(self):
        result = execute_python_code('print("before")\nraise ValueError("oops")')
        self.assertTrue(result["output"].startswith('before\nTraceback'))

    def test_stderr(self):
        self.assertEqual(execute_python_code('import sys\nprint("err", file=sys.stderr)')["output"], 'err\n')


if __name__ == "__main__":
    unittest.main()
