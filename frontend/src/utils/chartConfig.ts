/**
 * @fileoverview Shared chart configuration for Chart.js
 */

import { ChartOptions } from 'chart.js'
import { CHART_COLORS, CHART_PALETTE } from '../constants/colors'

/**
 * Base chart options for all charts
 */
export const baseChartOptions: ChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 1500,
    easing: 'easeInOutQuart',
  },
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: '#ffffff',
        padding: 15,
        font: { size: 12, family: 'Inter, sans-serif' },
        usePointStyle: true,
        pointStyle: 'circle',
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 18, 25, 0.98)',
      titleColor: '#ffffff',
      bodyColor: '#b3e5fc',
      borderColor: CHART_COLORS.primary,
      borderWidth: 2,
      padding: 15,
      displayColors: true,
      titleFont: { size: 14, weight: 'bold' },
      bodyFont: { size: 13 },
      cornerRadius: 8,
    }
  }
}

/**
 * Bar chart specific options
 */
export const barChartOptions: ChartOptions<'bar'> = {
  ...baseChartOptions,
  scales: {
    x: {
      ticks: {
        color: '#b3e5fc',
        font: { size: 10, family: 'Inter, sans-serif' }
      },
      grid: { color: 'rgba(33, 150, 243, 0.1)' }
    },
    y: {
      ticks: {
        color: '#b3e5fc',
        font: { family: 'Inter, sans-serif' }
      },
      grid: { color: 'rgba(33, 150, 243, 0.1)' }
    }
  }
}

/**
 * Line chart specific options
 */
export const lineChartOptions: ChartOptions<'line'> = {
  ...barChartOptions,
  elements: {
    line: {
      tension: 0.4,
      borderWidth: 3,
    },
    point: {
      radius: 6,
      hoverRadius: 8,
      borderWidth: 2,
    }
  }
}

/**
 * Pie chart specific options
 */
export const pieChartOptions: ChartOptions<'pie'> = {
  ...baseChartOptions,
}

/**
 * Doughnut chart specific options
 */
export const doughnutChartOptions: ChartOptions<'doughnut'> = {
  ...baseChartOptions,
  cutout: '65%',
  plugins: {
    ...baseChartOptions.plugins,
    legend: {
      position: 'right',
      labels: {
        color: '#ffffff',
        padding: 12,
        font: { size: 11, family: 'Inter, sans-serif' },
        usePointStyle: true,
        pointStyle: 'circle',
      }
    }
  }
}

/**
 * Create a dataset configuration for bar charts
 */
export function createBarDataset(
  data: number[],
  label: string,
  color: string = CHART_COLORS.primary
) {
  return {
    label,
    data,
    backgroundColor: color,
    borderColor: CHART_COLORS.primaryLight,
    borderWidth: 2,
    borderRadius: 8,
  }
}

/**
 * Create a dataset configuration for line charts
 */
export function createLineDataset(
  data: number[],
  label: string,
  color: string = CHART_COLORS.primary,
  fill: boolean = true
) {
  return {
    label,
    data,
    borderColor: color,
    backgroundColor: fill ? `${color}33` : 'transparent', // 33 = 20% opacity
    fill,
    tension: 0.4,
    borderWidth: 3,
    pointRadius: 6,
    pointHoverRadius: 8,
    pointBackgroundColor: color,
    pointBorderColor: '#ffffff',
    pointBorderWidth: 2,
  }
}

/**
 * Create a dataset configuration for pie/doughnut charts
 */
export function createPieDataset(data: number[], colors: readonly string[] = CHART_PALETTE) {
  return {
    data,
    backgroundColor: [...colors],
    borderColor: colors.map(color => color + '88'), // 88 = 50% opacity
    borderWidth: 2,
    hoverOffset: 15,
  }
}

export default {
  baseChartOptions,
  barChartOptions,
  lineChartOptions,
  pieChartOptions,
  doughnutChartOptions,
  createBarDataset,
  createLineDataset,
  createPieDataset,
}
