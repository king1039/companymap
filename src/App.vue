<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import companyData from '../companies_guangzhou.json'

interface Company {
  company_name: string
  poi_name: string | null
  address: string | null
  district: string | null
  lng: number | null
  lat: number | null
  status?: string
  website: string
  careerUrl: string
}

type CompanyRecord = Omit<Company, 'website' | 'careerUrl'>

const companyLinks: Record<string, Pick<Company, 'website' | 'careerUrl'>> = {
  微软: {
    website: 'https://www.microsoft.com',
    careerUrl: 'https://careers.microsoft.com',
  },
  甲骨文: {
    website: 'https://www.oracle.com',
    careerUrl: 'https://careers.oracle.com',
  },
  西门子: {
    website: 'https://www.siemens.com',
    careerUrl: 'https://jobs.siemens.com',
  },
  ABB: {
    website: 'https://global.abb',
    careerUrl: 'https://careers.abb',
  },
  艾默生: {
    website: 'https://www.emerson.com',
    careerUrl: 'https://www.emerson.com/careers',
  },
  施耐德电气: {
    website: 'https://www.se.com',
    careerUrl: 'https://careers.se.com',
  },
  赛默飞: {
    website: 'https://www.thermofisher.com',
    careerUrl: 'https://jobs.thermofisher.com',
  },
  汇丰: {
    website: 'https://www.hsbc.com',
    careerUrl: 'https://www.hsbc.com/careers',
  },
  渣打: {
    website: 'https://www.sc.com',
    careerUrl: 'https://www.sc.com/en/global-careers',
  },
  埃森哲: {
    website: 'https://www.accenture.com',
    careerUrl: 'https://www.accenture.com/careers',
  },
  德勤: {
    website: 'https://www2.deloitte.com',
    careerUrl: 'https://careers.deloitte.com',
  },
  毕马威: {
    website: 'https://home.kpmg',
    careerUrl: 'https://kpmg.com/careers',
  },
  普华永道: {
    website: 'https://www.pwc.com',
    careerUrl: 'https://www.pwc.com/careers',
  },
}

const includedPoiKeywords = ['有限公司', '分公司', '中心', '总部', '银行', '投资', '咨询', '国际金融']
const excludedPoiKeywords = ['专卖店', '体验馆', '维修店', '实验室', '烤肉', '柠檬茶', '体育用品', '照明']
const sourceCompanies = (companyData as CompanyRecord[]).map((company) => ({
  ...company,
  website: companyLinks[company.company_name]?.website ?? '',
  careerUrl: companyLinks[company.company_name]?.careerUrl ?? '',
}))
const companies = sourceCompanies.filter((company) => {
  const poiName = company.poi_name
  if (Object.hasOwn(company, 'status') || typeof poiName !== 'string') return false

  return (
    includedPoiKeywords.some((keyword) => poiName.includes(keyword)) &&
    !excludedPoiKeywords.some((keyword) => poiName.includes(keyword))
  )
})

const selectedCompanyId = ref<string | null>(null)
const mapElement = ref<HTMLDivElement | null>(null)

let map: AMap.Map | null = null
let infoWindow: AMap.InfoWindow | null = null
const markers = new Map<string, AMap.Marker>()

function openExternalLink(url: string): void {
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer')
}

function createLinkButton(
  label: string,
  unavailableLabel: string,
  url: string,
  styleClass: string,
): HTMLButtonElement {
  const button = document.createElement('button')
  button.type = 'button'
  button.className = `company-link ${styleClass}`
  button.textContent = url ? label : unavailableLabel
  button.disabled = !url
  if (url) button.addEventListener('click', () => openExternalLink(url))
  return button
}

function createInfoContent(company: Company): HTMLElement {
  const content = document.createElement('div')
  content.className = 'company-info'

  const title = document.createElement('h3')
  title.textContent = company.company_name
  content.append(title)

  const infoRows = [
    ['POI名称', company.poi_name],
    ['地址', company.address],
    ['区域', company.district],
  ]
  for (const [label, value] of infoRows) {
    const row = document.createElement('p')
    const rowLabel = document.createElement('span')
    rowLabel.textContent = label
    row.append(rowLabel, document.createTextNode(value ?? ''))
    content.append(row)
  }

  const actions = document.createElement('div')
  actions.className = 'company-info__actions'
  actions.append(
    createLinkButton('官网', '暂无官网', company.website, 'company-link--website'),
    createLinkButton('招聘', '暂无招聘', company.careerUrl, 'company-link--career'),
  )
  content.append(actions)

  return content
}

function selectCompany(company: Company): void {
  selectedCompanyId.value = company.company_name

  const marker = markers.get(company.company_name)
  if (!map || !marker || !infoWindow || company.lng === null || company.lat === null) return

  map.setCenter([company.lng, company.lat])
  infoWindow.setContent(createInfoContent(company))
  infoWindow.open(map, marker.getPosition())
}

onMounted(async () => {
  if (!mapElement.value) return

  const AMap = await AMapLoader.load({
    key: '71cf12fa49dc95a93d0be760a492b666',
    version: '2.0',
  })

  const currentMap = new AMap.Map(mapElement.value, {
    center: [113.2644, 23.1291],
    zoom: 11,
  })
  map = currentMap
  infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -30) })

  for (const company of companies) {
    if (company.lng === null || company.lat === null) continue

    const marker = new AMap.Marker({
      position: [company.lng, company.lat],
      title: company.company_name,
    })

    marker.on('click', () => selectCompany(company))
    markers.set(company.company_name, marker)
    currentMap.add(marker)
  }
})

onBeforeUnmount(() => {
  map?.destroy()
  map = null
  infoWindow = null
  markers.clear()
})
</script>

<template>
  <main class="company-map">
    <aside class="company-panel" aria-label="企业列表">
      <header class="panel-header">
        <p class="eyebrow">广州市</p>
        <h1>企业地图</h1>
        <div class="company-stats">
          <div class="company-stats__item">
            <span>总企业数</span>
            <strong>{{ sourceCompanies.length }}</strong>
          </div>
          <div class="company-stats__item">
            <span>有效企业数</span>
            <strong>{{ companies.length }}</strong>
          </div>
        </div>
      </header>

      <ul class="company-list">
        <li v-for="company in companies" :key="company.company_name">
          <div
            class="company-card"
            :class="{ 'company-card--active': selectedCompanyId === company.company_name }"
          >
            <button class="company-card__main" type="button" @click="selectCompany(company)">
              <span class="company-card__marker" aria-hidden="true"></span>
              <span class="company-card__content">
                <span class="company-card__name">{{ company.company_name }}</span>
                <span class="company-card__meta">{{ company.poi_name }}</span>
                <span class="company-card__address">{{ company.district }} · {{ company.address }}</span>
              </span>
              <span class="company-card__arrow" aria-hidden="true">›</span>
            </button>
            <div class="company-card__actions">
              <button
                class="company-link company-link--website"
                type="button"
                :disabled="!company.website"
                @click.stop="openExternalLink(company.website)"
              >
                {{ company.website ? '🌐 官网' : '暂无官网' }}
              </button>
              <button
                class="company-link company-link--career"
                type="button"
                :disabled="!company.careerUrl"
                @click.stop="openExternalLink(company.careerUrl)"
              >
                {{ company.careerUrl ? '💼 招聘' : '暂无招聘' }}
              </button>
            </div>
          </div>
        </li>
      </ul>
    </aside>

    <section class="map-area" aria-label="广州企业地图">
      <div ref="mapElement" class="map-container"></div>
      <div class="map-caption">
        <span class="map-caption__dot"></span>
        <span>广州市</span>
      </div>
    </section>
  </main>
</template>
