#!/usr/bin/env python3
"""

Description:
    A command-line program that generates Fibonacci sequences on demand.
    Supports various output formats including one-line display, numbering,
    and last-only options.

Usage:
    ./fibonacci-gen [-c|--count] 20 [--one-line] [--last-only] [--numbering] [--help]
"""

import argparse
import sys


def get_fibonacci(n):
    """
    Generate the first n numbers in the Fibonacci sequence.
    
    Args:
        n (int): The count of Fibonacci numbers to generate.
                 Must be a positive integer.
    
    Returns:
        list: A list containing the first n Fibonacci numbers.
        
    Raises:
        ValueError: If n is negative or not an integer.
        
    Examples:
        >>> get_fibonacci(6)
        [0, 1, 1, 2, 3, 5]
    """
    if not isinstance(n, int):
        raise ValueError("Count must be an integer")
    if n < 0:
        raise ValueError("Count must be non-negative")
    if n == 0:
        return []
    
    sequence = []
    a, b = 0, 1
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    return sequence


def main():
    """
    Main entry point for the Fibonacci generator program.
    
    Parses command-line arguments and outputs Fibonacci sequences
    according to user specifications.
    
    Exit Codes:
        0: Successful execution
        1: Invalid arguments or error
    """
    parser = argparse.ArgumentParser(
        prog='Fibonacci-gen',
        description='Fibonacci sequence generator',
        add_help=False
    )
    
    parser.add_argument(
        '--help',
        action='help',
        help='Print this help message'
    )
    parser.add_argument(
        '-c', '--count',
        type=int,
        metavar='COUNT',
        help='Calculate to this many places. Example: -c 6 produces 0, 1, 1, 2, 3, 5'
    )
    parser.add_argument(
        '--one-line',
        action='store_true',
        help='Print all numbers on one line, separated by commas'
    )
    parser.add_argument(
        '--numbering',
        action='store_true',
        help='Preface each number with its placement (1-indexed). Example: 1:0, 2:1, 3:1'
    )
    parser.add_argument(
        '--last-only',
        action='store_true',
        help='Only print the last number in the sequence'
    )

    args = parser.parse_args()

    # Validate that count was provided
    if args.count is None:
        parser.print_help()
        return

    # Validate count is positive
    if args.count < 0:
        print("Error: --count must be a non-negative integer", file=sys.stderr)
        sys.exit(1)

    try:
        sequence = get_fibonacci(args.count)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Handle --last-only flag
    if args.last_only:
        if sequence:
            print(sequence[-1])
        return

    # Build output with optional numbering
    output = []
    for i, val in enumerate(sequence):
        if args.numbering:
            entry = f"{i+1}:{val}"
        else:
            entry = str(val)
        output.append(entry)

    # Print results
    if args.one_line:
        print(", ".join(output))
    else:
        for item in output:
            print(item)


if __name__ == "__main__":
    main()
