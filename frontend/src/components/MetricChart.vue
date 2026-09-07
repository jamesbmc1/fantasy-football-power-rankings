<script setup lang="ts">
import { computed } from 'vue'
import type { ApexOptions } from 'apexcharts'
const props = withDefaults(defineProps<{
  categories: string[]
  series: { name: string; data: number[] }[]
  kind?: 'line' | 'bar'
  horizontal?: boolean
  reversed?: boolean
  min?: number
  max?: number
  average?: number
  referenceLabel?: string
  integer?: boolean
  colors?: string[]
  distributed?: boolean
  height?: number
  label: string
}>(), { kind: 'line', height: 280, horizontal: false, reversed: false, integer: false, distributed: false })
const options = computed<ApexOptions>(() => ({
  chart: { background: 'transparent', toolbar: { show: false }, animations: { enabled: false }, fontFamily: 'inherit' },
  theme: { mode: 'dark' },
  colors: props.colors || ['#d9bd83', '#a7a7af'],
  stroke: { curve: 'straight', width: props.kind === 'line' ? 2 : 0, dashArray: props.series.map((_, i) => i ? 5 : 0) },
  markers: { size: props.kind === 'line' ? 3 : 0 },
  dataLabels: { enabled: false },
  plotOptions: { bar: { horizontal: props.horizontal, distributed: props.distributed, borderRadius: 3, barHeight: '55%' } },
  grid: { borderColor: '#2a2a30', strokeDashArray: 4 },
  xaxis: { categories: props.categories, ...(props.horizontal ? { min: props.min, max: props.max, tickAmount: 4 } : {}), labels: { style: { colors: '#aaaab2' }, ...(props.horizontal ? { formatter: (v: string) => Number(v).toFixed(1) } : {}) }, axisBorder: { show: false }, axisTicks: { show: false } },
  yaxis: { reversed: props.reversed, ...(!props.horizontal ? { min: props.min, max: props.max } : {}), ...(props.integer && props.min !== undefined && props.max !== undefined ? { tickAmount: Math.max(1, props.max - props.min) } : {}), labels: { style: { colors: '#aaaab2' }, ...(!props.horizontal ? { formatter: (v: number) => props.integer ? String(Math.round(v)) : v.toFixed(1) } : {}) } },
  annotations: props.horizontal && props.average !== undefined ? { xaxis: [{ x: props.average, borderColor: '#d9bd83', strokeDashArray: 4, label: { text: props.referenceLabel || `League average ${props.average.toFixed(1)}`, style: { background: '#252529', color: '#eee' } } }] } : {},
  legend: { show: !props.distributed && props.series.length > 1, position: 'top', labels: { colors: '#c0c0c7' } },
  tooltip: { theme: 'dark', y: { formatter: (v: number) => props.integer ? String(Math.round(v)) : v.toFixed(2) } },
}))
</script>
<template><div role="img" :aria-label="label"><apexchart :type="kind" :height="height" :options="options" :series="series" /></div></template>
