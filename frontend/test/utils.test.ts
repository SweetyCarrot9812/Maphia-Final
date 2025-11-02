/**
 * Tests for utility functions
 */

import { describe, it, expect } from 'vitest';
import {
  cn,
  formatFileSize,
  formatDate,
  formatNumber,
  truncate,
} from '@/lib/utils';

describe('cn utility', () => {
  it('should merge class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('should handle conditional classes', () => {
    expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz');
  });

  it('should merge Tailwind classes correctly', () => {
    expect(cn('px-2 py-1', 'px-4')).toBe('py-1 px-4');
  });
});

describe('formatFileSize', () => {
  it('should format bytes', () => {
    expect(formatFileSize(500)).toBe('500 bytes');
  });

  it('should format KB', () => {
    expect(formatFileSize(1024)).toBe('1.00 KB');
    expect(formatFileSize(2048)).toBe('2.00 KB');
  });

  it('should format MB', () => {
    expect(formatFileSize(1024 * 1024)).toBe('1.00 MB');
    expect(formatFileSize(5 * 1024 * 1024)).toBe('5.00 MB');
  });

  it('should format GB', () => {
    expect(formatFileSize(1024 * 1024 * 1024)).toBe('1.00 GB');
    expect(formatFileSize(2.5 * 1024 * 1024 * 1024)).toBe('2.50 GB');
  });
});

describe('formatDate', () => {
  it('should format ISO date string', () => {
    const date = '2025-01-15T10:30:00Z';
    const formatted = formatDate(date);

    expect(formatted).toContain('2025');
    expect(formatted).toContain('1');
    expect(formatted).toContain('15');
  });

  it('should handle different date formats', () => {
    const date = '2025-12-25T23:59:59Z';
    const formatted = formatDate(date);

    expect(formatted).toBeTruthy();
    expect(typeof formatted).toBe('string');
  });
});

describe('formatNumber', () => {
  it('should format numbers with thousand separators', () => {
    expect(formatNumber(1000)).toBe('1,000');
    expect(formatNumber(1234567)).toBe('1,234,567');
  });

  it('should handle small numbers', () => {
    expect(formatNumber(0)).toBe('0');
    expect(formatNumber(999)).toBe('999');
  });

  it('should handle decimal numbers', () => {
    const formatted = formatNumber(1234.56);
    expect(formatted).toContain('1');
    expect(formatted).toContain('234');
  });
});

describe('truncate', () => {
  it('should truncate long strings', () => {
    const longString = 'This is a very long string that needs truncation';
    expect(truncate(longString, 20)).toBe('This is a very lo...');
  });

  it('should not truncate short strings', () => {
    const shortString = 'Short';
    expect(truncate(shortString, 20)).toBe('Short');
  });

  it('should handle exact length', () => {
    const string = '12345678901234567890';
    expect(truncate(string, 20)).toBe('12345678901234567890');
  });

  it('should handle edge case with maxLength <= 3', () => {
    expect(truncate('Hello', 3)).toBe('...');
  });
});
