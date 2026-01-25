import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const STATE_PATH = './note-state.json';

const wait = (ms) => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('note.comログインページに遷移します...');
  await page.goto('https://note.com/login');

  console.log('手動でログインしてください。ログイン完了を自動検知します...');

  // ログイン完了を自動検知（note.comのトップページに遷移するまで待機）
  try {
    await page.waitForURL(/note\.com\/?$/, { timeout: 300000 }); // 5分待機
    console.log('ログイン完了を検知しました！');
  } catch (error) {
    console.log('ログイン完了の検知がタイムアウトしました。');
    console.log('手動でEnterキーを押してください。');
    await new Promise(resolve => {
      process.stdin.once('data', () => {
        resolve();
      });
    });
  }

  console.log('ログイン状態を確認中...');

  // 現在のURLを確認
  console.log(`Current URL: ${page.url()}`);

  // 記事作成ページに遷移してセッションが有効か確認
  console.log('記事作成ページに遷移してセッションを確認します...');
  await page.goto('https://note.com/notes/new');
  await page.waitForLoadState('networkidle');
  await wait(3000);

  // ログインページにリダイレクトされていないか確認
  const currentUrl = page.url();
  console.log(`Current URL after navigation: ${currentUrl}`);

  if (currentUrl.includes('/login')) {
    console.log('❌ セッションが無効です。再度ログインしてください。');
    await browser.close();
    process.exit(1);
  }

  console.log('✓ セッションが有効です！記事作成ページにアクセスできました。');

  // セッション状態を保存
  await context.storageState({ path: STATE_PATH });
  console.log(`✓ セッション状態を保存しました: ${STATE_PATH}`);

  // 保存されたファイルのサイズを確認
  const fsModule = await import('fs');
  const stats = fsModule.statSync(STATE_PATH);
  console.log(`File size: ${stats.size} bytes`);

  // 保存されたクッキーの数を確認
  const stateData = JSON.parse(fsModule.readFileSync(STATE_PATH, 'utf-8'));
  console.log(`Cookies saved: ${stateData.cookies.length}`);

  await browser.close();
  console.log('ブラウザを閉じました。');
})();
