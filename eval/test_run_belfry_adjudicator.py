"""Test that run_belfry correctly handles adjudicator arguments."""

from __future__ import annotations

import argparse
import unittest

from eval.run_belfry import main  # Import to trigger argument parsing


class TestRunBelfryAdjudicator(unittest.TestCase):
    """Test adjudicator argument handling in run_belfry."""

    def test_adjudicator_argument_exists(self):
        """Test that --adjudicator argument is available."""
        # This will fail initially since we haven't implemented it yet
        try:
            # Try to parse --adjudicator argument
            import sys
            original_argv = sys.argv
            sys.argv = ['run_belfry.py', '--adjudicator', 'random']
            try:
                main()
            except SystemExit as e:
                # main() calls sys.exit() when done, which is expected
                if e.code != 0:
                    raise  # Re-raise if it's an error exit
            finally:
                sys.argv = original_argv
            self.assertTrue(True)  # If we get here without error, the argument exists
        except SystemExit as e:
            if e.code != 0:
                self.fail("--adjudicator argument not recognized or caused error")
            # If exit code is 0, it's okay - means parsing succeeded and main exited normally
        except Exception as e:
            # Other exceptions might occur (like missing backend for llm), but that's okay
            # for the random adjudicator test
            if "needs --backend" not in str(e):
                raise  # Re-raise if it's not the expected backend error

    def test_adjudicator_choices(self):
        """Test that valid adjudicator choices are accepted."""
        # Test the choices we expect to implement
        valid_choices = ['random']  # Start with random since llm needs backend
        for choice in valid_choices:
            with self.subTest(choice=choice):
                try:
                    import sys
                    original_argv = sys.argv
                    sys.argv = ['run_belfry.py', '--adjudicator', choice, '--games', '1']
                    try:
                        main()
                    except SystemExit as e:
                        # main() calls sys.exit() when done
                        if e.code != 0 and "needs --backend" not in str(e):
                            raise  # Re-raise if it's an unexpected error
                    finally:
                        sys.argv = original_argv
                except SystemExit as e:
                    if e.code != 0 and "needs --backend" not in str(e):
                        self.fail(f"--adjudicator {choice} not recognized or caused unexpected error")
                except Exception as e:
                    if "needs --backend" not in str(e):
                        raise  # Re-raise if it's not the expected backend error


if __name__ == '__main__':
    unittest.main()