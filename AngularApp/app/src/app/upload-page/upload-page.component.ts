import { Component, OnInit, AfterViewInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-upload-page',
  templateUrl: './upload-page.component.html',
  styleUrls: ['./upload-page.component.css']
})

export class UploadPageComponent implements OnInit, AfterViewInit {

  spinner: HTMLElement
  upload_button: HTMLElement
  warning_message: HTMLElement

  constructor(private router: Router) { 
  }

  ngOnInit(): void {
  }

  ngAfterViewInit() {
    this.upload_button = document.getElementById('upload_button')!
    this.spinner = document.getElementById('spinner')!
    this.warning_message = document.getElementById('warn_message')!
  }

  upload_logs() {
    this.disable_upload_button()
    this.spinner.classList.remove('invisible')
    this.warning_message.classList.add('invisible')

    let formElement = document.getElementById('formElement')

    formElement!.onsubmit = async (e) => {

      e.preventDefault();

      let response = await fetch('/api/upload', {
        method: 'POST',
        body: new FormData(formElement as HTMLFormElement)
      });

      let result = await response.json();

      if (result["status"] == "ok") this.router.navigate(['dashboard']);
      if (result["status"] == "wrong format") {
        this.warning_message.classList.remove('invisible')
        this.spinner.classList.add('invisible')
        this.enable_upload_button()
      };
    }
  }

  enable_upload_button() {
    this.upload_button.classList.remove('disabled')
  }

  disable_upload_button() {
    this.upload_button.classList.add('disabled')
  }
}
