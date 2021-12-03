import { Component, OnInit, AfterViewInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit, AfterViewInit {
  categories: any
  items: any
  category_index: number = 0
  server_load_data: any = {
    loaded: false
  }
  actions_per_country_data: any = {
    country: [],
    actions: []
  }
  unpayed_carts: any = {
    loaded: false,
    list: []
  }
  repeat_purchases: any = {
    loaded: false,
    ip_list: [],
    amount: []
  }
  time_pattern: any = {
    loaded: false,
    amount: []
  }
  pattern_view: any = {
    country: [],
    actions: []
  }
  pattern_buy: any = {
    category: [],
    purchases: []
  }


  constructor(private router: Router) {
  }

  ngOnInit(): void {
    if (!this.check_db())
      return
    this.get_categories()
    this.get_filename()
    setTimeout(this.getOverallStatistics, 1000);
  }

  ngAfterViewInit() {
    //setTimeout(this.getOverallStatistics, 1000);
  }

  async getOverallStatistics() {
    let response = await fetch('/api/overall_statistics', {
      method: 'GET'
    });

    let overall_statistics = await response.json();

    let countries = overall_statistics['countries']
    let items_views = overall_statistics['items_views']
    let payed_carts = overall_statistics['payed_carts']
    let unique_users = overall_statistics['unique_users']


    document.getElementById("countries")!.style.setProperty("--num", countries as string)
    document.getElementById("items_views")!.style.setProperty("--num", items_views as string)
    document.getElementById("payed_carts")!.style.setProperty("--num", payed_carts as string)
    document.getElementById("unique_users")!.style.setProperty("--num", unique_users as string)
  }

  async check_db() {
    let response = await fetch('api/check_db', {
      method: 'GET'
    });

    if (response.status == 204) {
      this.router.navigate([''])
      return false
    }
    return true
  }

  async get_categories() {

    let response = await fetch('/api/categories', {
      method: 'GET'
    })

    let result = await response.json()
    this.categories = Object.keys(result)
    this.items = Object.values(result)
  }

  async get_filename() {
    let response = await fetch('/api/uploaded_filename', {
      method: 'GET'
    })

    let result = await response.json()
    let filename = result['filename']
    document.getElementById('filename')!.textContent = filename;
  }

  update_items_list() {
    let category_select = document.getElementById("category_select")! as HTMLSelectElement
    let item_select = document.getElementById("item_select")! as HTMLSelectElement
    this.category_index = category_select.options[category_select.selectedIndex].value as unknown as number

    item_select.removeAttribute('disabled')

    document.getElementById('rep_time_pattern_button')!.removeAttribute('disabled')
  }

  enable_reports_buttons() {
    document.getElementById('rep_pattern_view_button')!.removeAttribute('disabled')
    document.getElementById('rep_pattern_buy_button')!.removeAttribute('disabled')
  }

  check_for_button_unlock(id: number) {
    let date1 = (document.getElementById(`rep${id}_date1`)! as HTMLInputElement).value
    let date2 = (document.getElementById(`rep${id}_date2`)! as HTMLInputElement).value
    let button = document.getElementById(`rep${id}_button`)!
    if (date1 && date2)
      button.removeAttribute('disabled')
    else
      button.setAttribute('disabled', 'true')
  }

  debug() {
    let data = {
      "canned_food": [
        "midii",
        "pate_of_tuna"
      ],
      "caviar": [
        "squash_caviar",
        "black_caviar"
      ],
      "fresh_fish": [
        "tuna",
        "codfish",
        "herring",
        "salmon",
        "crucian"
      ],
      "frozen_fish": [
        "shark",
        "pike",
        "peljad"
      ],
      "semi_manufactures": [
        "soup_set",
        "squid_rings",
        "salmon_cutlet"
      ]
    }
    this.categories = Object.keys(data)
    this.items = Object.values(data)


    let server_load_data = {
      "avg": "57.2857142857142857",
      "statistics": [
        {
          "day": 1.0,
          "hour": 0.0,
          "requests_amount": 55
        },
        {
          "day": 1.0,
          "hour": 1.0,
          "requests_amount": 67
        },
        {
          "day": 1.0,
          "hour": 2.0,
          "requests_amount": 62
        },
        {
          "day": 1.0,
          "hour": 3.0,
          "requests_amount": 57
        },
        {
          "day": 1.0,
          "hour": 4.0,
          "requests_amount": 62
        },
        {
          "day": 1.0,
          "hour": 5.0,
          "requests_amount": 69
        },
        {
          "day": 1.0,
          "hour": 6.0,
          "requests_amount": 29
        }
      ]
    }
    this.server_load_data = server_load_data;

  }

  async rep_server_load() {
    let response = await fetch('/api/server_load_per_hour', {
      method: 'GET'
    });

    let result = await response.json()
    result['loaded'] = true;
    this.server_load_data = result;
  }

  async rep_actions_per_country() {
    let response = await fetch('/api/rep_actions_per_country', {
      method: 'GET'
    })

    let result = await response.json()
    this.actions_per_country_data['country'] = Object.keys(result)
    this.actions_per_country_data['actions'] = Object.values(result)
  }

  async rep_unpayed_carts() {
    let query = {
      "date_1": (document.getElementById("rep1_date1") as HTMLSelectElement)!.value,
      "date_2": (document.getElementById("rep1_date2") as HTMLSelectElement)!.value,
    }

    let response = await fetch(`/api/rep_unpayed_carts?date_1=${query['date_1']}&date_2=${query['date_2']}`, {
      method: 'GET',
    });

    let result = await response.json();
    let res = {
      'list': result,
      'loaded': true
    }
    this.unpayed_carts = res;
   
  }

  async rep_repeat_purchases() {
    let query = {
      "date_1": (document.getElementById("rep2_date1") as HTMLSelectElement)!.value,
      "date_2": (document.getElementById("rep2_date2") as HTMLSelectElement)!.value,
    }

    let response = await fetch(`/api/rep_repeated_payments?date_1=${query['date_1']}&date_2=${query['date_2']}`, {
      method: 'GET',
    });

    let result = await response.json();

    let res = {
      ip_list: Object.keys(result['data']),
      amount: Object.values(result['data']),
      loaded: true,
      total_amount: result['amount']
    }

    this.repeat_purchases = res;

  }

  async rep_time_pattern() {

    let category = this.categories[this.category_index]
    let k_select = document.getElementById("k_select")! as HTMLSelectElement
    let k = k_select.options[k_select.selectedIndex].value as unknown as number

    k = 24 / k

    let response = await fetch(`/api/rep_time_pattern?category=${category}&k=${k}`, {
      method: 'GET',
    });

    let result = await response.json();

    this.time_pattern['amount'] = []
    for (let amount of Object.values(result)) {
      this.time_pattern['amount'].push(amount)
    }
    this.time_pattern.loaded = true

  }

  async rep_pattern_view() {

    let category = this.categories[this.category_index]
    let item_select = document.getElementById("item_select")! as HTMLSelectElement
    let item = item_select.options[item_select.selectedIndex].value

    let response = await fetch(`/api/rep_pattern_view?category=${category}&item=${item}`, {
      method: 'GET'
    })

    let result = await response.json()
    this.pattern_view['country'] = Object.keys(result)
    this.pattern_view['actions'] = Object.values(result)
  }

  async rep_pattern_buy() {

    let category = this.categories[this.category_index]
    let item_select = document.getElementById("item_select")! as HTMLSelectElement
    let item = item_select.options[item_select.selectedIndex].value

    let response = await fetch(`/api/rep_pattern_buy?category=${category}&item=${item}`, {
      method: 'GET'
    })

    let result = await response.json()
    this.pattern_buy['category'] = Object.keys(result)
    this.pattern_buy['purchases'] = Object.values(result)
  }
}
