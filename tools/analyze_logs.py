"""
Log Analysis Tool - Story 4.2

Analyzes JSON log files from Reachy Recognizer to generate
performance and accuracy reports.

Usage:
    python tools/analyze_logs.py <log_file>
    python tools/analyze_logs.py logs/reachy_recognizer.log
    python tools/analyze_logs.py logs/reachy_recognizer.log --export report.json
"""

import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import List, Dict, Any
import statistics


class LogAnalyzer:
    """Analyze JSON logs and generate reports."""
    
    def __init__(self, log_file: Path):
        """
        Initialize analyzer with log file.
        
        Args:
            log_file: Path to JSON log file
        """
        self.log_file = log_file
        self.events = []
        self.metrics_data = defaultdict(list)
        self.event_counts = Counter()
        self.errors = []
        self.warnings = []
        
    def parse_logs(self):
        """Parse JSON log file and extract data."""
        print(f"Parsing log file: {self.log_file}")
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    log_entry = json.loads(line)
                    self.events.append(log_entry)
                    
                    # Count event types
                    if 'event' in log_entry:
                        self.event_counts[log_entry['event']] += 1
                    
                    # Collect metrics
                    if 'metrics' in log_entry:
                        for key, value in log_entry['metrics'].items():
                            if isinstance(value, (int, float)):
                                self.metrics_data[key].append(value)
                    
                    # Track errors and warnings
                    if log_entry.get('level') == 'ERROR':
                        self.errors.append(log_entry)
                    elif log_entry.get('level') == 'WARNING':
                        self.warnings.append(log_entry)
                        
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse line {line_num}: {e}")
                    continue
                except Exception as e:
                    print(f"Warning: Error processing line {line_num}: {e}")
                    continue
        
        print(f"✓ Parsed {len(self.events)} log entries")
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report.
        
        Returns:
            Dictionary containing analysis results
        """
        report = {
            'summary': self._generate_summary(),
            'events': self._analyze_events(),
            'performance': self._analyze_performance(),
            'accuracy': self._analyze_accuracy(),
            'errors': self._analyze_errors(),
            'warnings': self._analyze_warnings()
        }
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate overview summary."""
        if not self.events:
            return {'total_entries': 0, 'time_range': None}
        
        timestamps = [
            e['timestamp'] for e in self.events 
            if 'timestamp' in e
        ]
        
        if timestamps:
            start_time = min(timestamps)
            end_time = max(timestamps)
            duration = self._parse_timestamp(end_time) - self._parse_timestamp(start_time)
        else:
            start_time = end_time = None
            duration = None
        
        return {
            'total_entries': len(self.events),
            'start_time': start_time,
            'end_time': end_time,
            'duration_seconds': duration.total_seconds() if duration else 0,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
    
    def _analyze_events(self) -> Dict[str, Any]:
        """Analyze event distribution."""
        return {
            'event_counts': dict(self.event_counts),
            'total_events': sum(self.event_counts.values()),
            'event_types': len(self.event_counts)
        }
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics."""
        performance = {}
        
        for metric_name, values in self.metrics_data.items():
            if not values:
                continue
            
            performance[metric_name] = {
                'count': len(values),
                'mean': round(statistics.mean(values), 2),
                'median': round(statistics.median(values), 2),
                'min': round(min(values), 2),
                'max': round(max(values), 2),
                'stdev': round(statistics.stdev(values), 2) if len(values) > 1 else 0
            }
        
        return performance
    
    def _analyze_accuracy(self) -> Dict[str, Any]:
        """Analyze recognition accuracy from events."""
        accuracy_events = [
            e for e in self.events 
            if e.get('event') == 'accuracy_update'
        ]
        
        if not accuracy_events:
            return {'note': 'No accuracy data found in logs'}
        
        # Get latest accuracy metrics
        latest = accuracy_events[-1]
        if 'metrics' in latest:
            return latest['metrics']
        
        return {'note': 'Accuracy data structure not found'}
    
    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze errors."""
        if not self.errors:
            return {'count': 0, 'recent': []}
        
        recent_errors = []
        for error in self.errors[-10:]:  # Last 10 errors
            recent_errors.append({
                'timestamp': error.get('timestamp'),
                'module': error.get('module'),
                'message': error.get('message')
            })
        
        return {
            'count': len(self.errors),
            'recent': recent_errors
        }
    
    def _analyze_warnings(self) -> Dict[str, Any]:
        """Analyze warnings."""
        if not self.warnings:
            return {'count': 0}
        
        return {
            'count': len(self.warnings),
            'sample': self.warnings[-5:] if len(self.warnings) <= 5 else []
        }
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse ISO 8601 timestamp."""
        # Remove 'Z' suffix if present
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1]
        return datetime.fromisoformat(timestamp_str)
    
    def print_report(self, report: Dict[str, Any]):
        """
        Print human-readable report to console.
        
        Args:
            report: Analysis report dictionary
        """
        print(f"\n{'='*80}")
        print(f"Log Analysis Report: {self.log_file.name}")
        print(f"{'='*80}\n")
        
        # Summary
        summary = report['summary']
        print("📊 Summary")
        print(f"  Total Log Entries: {summary['total_entries']}")
        if summary.get('duration_seconds'):
            print(f"  Duration: {summary['duration_seconds']:.1f} seconds")
        print(f"  Errors: {summary['error_count']}")
        print(f"  Warnings: {summary['warning_count']}\n")
        
        # Events
        events = report['events']
        print("📢 Events")
        print(f"  Total Events: {events['total_events']}")
        if events['event_counts']:
            print("  Event Breakdown:")
            for event_type, count in sorted(events['event_counts'].items(), key=lambda x: x[1], reverse=True):
                print(f"    {event_type}: {count}")
        print()
        
        # Performance
        performance = report['performance']
        if performance:
            print("⚡ Performance Metrics")
            for metric_name, stats in performance.items():
                print(f"  {metric_name}:")
                print(f"    Mean: {stats['mean']:.2f}")
                print(f"    Median: {stats['median']:.2f}")
                print(f"    Range: {stats['min']:.2f} - {stats['max']:.2f}")
                if stats['stdev'] > 0:
                    print(f"    Std Dev: {stats['stdev']:.2f}")
            print()
        
        # Accuracy
        accuracy = report['accuracy']
        if 'recognized_count' in accuracy:
            print("🎯 Recognition Accuracy")
            print(f"  Recognized: {accuracy.get('recognized_count', 0)}")
            print(f"  Unknown: {accuracy.get('unknown_count', 0)}")
            print(f"  True Positives: {accuracy.get('true_positives', 0)}")
            print(f"  True Negatives: {accuracy.get('true_negatives', 0)}")
            if 'accuracy' in accuracy:
                print(f"  Accuracy: {accuracy['accuracy']:.2f}%")
            if 'note' in accuracy:
                print(f"  Note: {accuracy['note']}")
            print()
        
        # Errors
        errors = report['errors']
        if errors['count'] > 0:
            print(f"❌ Errors ({errors['count']} total)")
            if errors.get('recent'):
                print("  Recent Errors:")
                for error in errors['recent'][-5:]:
                    print(f"    [{error.get('timestamp', 'N/A')}] {error.get('message', 'No message')}")
            print()
        
        # Warnings
        warnings = report['warnings']
        if warnings['count'] > 0:
            print(f"⚠️  Warnings: {warnings['count']}\n")
        
        print(f"{'='*80}\n")
    
    def export_report(self, report: Dict[str, Any], output_file: Path):
        """
        Export report to JSON file.
        
        Args:
            report: Analysis report dictionary
            output_file: Output file path
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"✓ Report exported to: {output_file}")


def main():
    """Main entry point for log analysis tool."""
    parser = argparse.ArgumentParser(
        description='Analyze Reachy Recognizer JSON logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/analyze_logs.py logs/reachy_recognizer.log
  python tools/analyze_logs.py logs/reachy_recognizer.log --export report.json
        """
    )
    
    parser.add_argument(
        'log_file',
        type=str,
        help='Path to JSON log file'
    )
    
    parser.add_argument(
        '--export',
        type=str,
        help='Export report to JSON file'
    )
    
    args = parser.parse_args()
    
    # Validate log file
    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"Error: Log file not found: {log_path}")
        sys.exit(1)
    
    # Analyze logs
    analyzer = LogAnalyzer(log_path)
    analyzer.parse_logs()
    
    report = analyzer.generate_report()
    analyzer.print_report(report)
    
    # Export if requested
    if args.export:
        output_path = Path(args.export)
        analyzer.export_report(report, output_path)


if __name__ == "__main__":
    main()
