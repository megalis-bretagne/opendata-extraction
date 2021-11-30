import download = require('download');
import { readFileSync, writeFileSync } from 'fs';
import * as Iconv from 'iconv';
import { JSDOM } from 'jsdom';
import { TextDecoder } from 'util';

import { downloadAndSave } from './download';

const NORMES_BUDGETAIRE_URL: string = 'http://odm-budgetaire.org/composants/normes';

const outputDirectory: string = 'output';

async function main() {
  const years = await listYears();

  for (const year of years) {
    const codes = await listCodes(year);

    for (const code of codes) {
      const formats = await listFormats(year, code);

      for (const format of formats) {
        await downloadPlanDeCompte(year, code, format);
      }

    }

  }
}

async function downloadPlanDeCompte(year: string, code: string, format: string): Promise<void> {
  const planDeCompteFileName: string = `${year}/${code}/${format}/planDeCompte.xml`;
  try {

    await downloadAndSave(planDeCompteFileName, NORMES_BUDGETAIRE_URL, outputDirectory);
    convertXmlToUtf8(`${outputDirectory}/${planDeCompteFileName}`);
  } catch {
    console.log(`Failed to download ${planDeCompteFileName}`);
  }
}

async function listYears(): Promise<string[]> {
  return listDirectory(`${NORMES_BUDGETAIRE_URL}`, /^(\d\d\d\d)\/$/i);
}

async function convertXmlToUtf8(xmlFileName: string): Promise<void> {
  const content: Buffer = readFileSync(xmlFileName);
  const iconv: any = new Iconv.Iconv('ISO-8859-1', 'UTF-8');
  const buffer: Buffer = iconv.convert(content);
  const file: string = buffer.toString('utf8');

  const regexp: RegExp = /<\?xml version='1\.0' encoding='(.*)'\?>/i;
  const fileUtf8: string = file.replace(regexp, (a, b) => '<?xml version=\'1.0\' encoding=\'UTF-8\'?>');

  writeFileSync(`${xmlFileName}`, fileUtf8);
}

async function listCodes(year: string): Promise<string[]> {
  return listDirectory(`${NORMES_BUDGETAIRE_URL}/${year}`, /^(M\d+)\/$/i);
}

async function listFormats(year: string, code: string): Promise<string[]> {
  return listDirectory(`${NORMES_BUDGETAIRE_URL}/${year}/${code}`, /^(M\d+(?:_.*)?)\/$/i);
}

async function listDirectory(url: string, regex: RegExp): Promise<string[]> {
  const htmlBuffer: any = await download(url);

  const enc: TextDecoder = new TextDecoder('utf-8');
  const htmlStr: string = enc.decode(htmlBuffer);

  const dom: JSDOM = new JSDOM(htmlStr);

  const links: any = Array.prototype.slice.call(dom.window.document.body.children[2].children);

  const results: string[] = [];
  for (const link of links) {
    const href: string = link.getAttribute('href');

    const matchResult: RegExpExecArray | null = regex.exec(href);
    if (matchResult) {
      results.push(matchResult[1]);
    }
  }

  return results;
}

main().catch(
  (error) => {
    console.error(error);
    process.exit(1);
  }
);
