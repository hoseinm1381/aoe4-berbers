// Editable SVG presentation composition. Raster masters are preserved.
import fs from 'node:fs';import path from 'node:path';import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const sharp=require(process.env.GARRISON_SHARP||'sharp');
const base=path.resolve(process.argv[2]||path.join(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(?:([A-Z]:))/, '$1')),'..'));const config=JSON.parse(fs.readFileSync(path.join(base,'project.json'),'utf8'));
const surfaces={flag_list:[104,56],flag_list_small:[52,28],flag_secondary:[440,248],flag_secondary_small:[220,124],flag_fade:[344,104],flag_loading:[1920,1080],flag_pattern:[1120,352],flag_tile:[736,800],flag_mastery:[1112,588]};
for(const civ of [config.race]){
 const root=path.join(base,'source/presentation');const hd=path.join(root,'hd');
 if(civ==='korea')await sharp(path.join(hd,'flag.svg')).png().toFile(path.join(hd,'flag.png'));
 const master=fs.readFileSync(path.join(hd,'flag.png'));const data='data:image/png;base64,'+master.toString('base64');
 const colors={korea:'#c00d45',persia:'#087012',vietnam:'#bd8b14',berbers:'#288b7a'};
 const out=path.join(root,'derived_011');fs.mkdirSync(out,{recursive:true});
 async function render(name,w,h){
  const loading=name==='flag_loading';const faded=['flag_pattern','flag_fade'].includes(name);
  const image=loading&&civ==='korea'?`<image href="../hd/flag.png" x="${w-h}" width="${h}" height="${h}"/>`:`<image href="../hd/flag.png" width="${w}" height="${h}" preserveAspectRatio="xMidYMid ${loading||faded?'slice':'meet'}"/>`;
  const gradient=`<linearGradient id="shade"><stop offset="0" stop-color="#07101c" stop-opacity="0.97"/><stop offset="0.35" stop-color="#07101c" stop-opacity="0.89"/><stop offset="0.58" stop-color="#07101c" stop-opacity="0.5"/><stop offset="0.85" stop-color="#07101c" stop-opacity="0.04"/><stop offset="1" stop-color="#07101c" stop-opacity="0"/></linearGradient>`;
  const mask=`<linearGradient id="alpha"><stop offset="0" stop-color="black"/><stop offset="0.3" stop-color="black"/><stop offset="0.82" stop-color="white"/></linearGradient><mask id="fade"><rect width="${w}" height="${h}" fill="url(#alpha)"/></mask>`;
  let svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><defs>${gradient}${mask}</defs><g${faded?' mask="url(#fade)"':''}><rect width="${w}" height="${h}" fill="${colors[civ]}"/>${image}</g>${loading?`<rect width="${w}" height="${h}" fill="url(#shade)"/>`:''}</svg>`;
  fs.writeFileSync(path.join(out,name+'.svg'),svg);
  const png=await sharp(Buffer.from(svg.replaceAll('../hd/flag.png',data))).png({compressionLevel:9}).toBuffer();
  fs.writeFileSync(path.join(out,name+'.png'),png);return {name,width:w,height:h,bytes:png.length};
 }
 const rows=[];for(const [name,[w,h]] of Object.entries(surfaces))rows.push(await render(name,w,h));
 const cover=await render('cover',1920,1080);fs.copyFileSync(path.join(out,'cover.png'),path.join(root,'cover.png'));
 if(cover.bytes>4*1024*1024){if(master.length>4*1024*1024)throw Error('Client master exceeds 4 MiB');fs.writeFileSync(path.join(root,'cover.png'),master);cover.bytes=master.length;}
 fs.writeFileSync(path.join(root,'presentation-011.json'),JSON.stringify({version:'0.1.1',master:'hd/flag.png',surfaces:rows,client_cover_bytes:cover.bytes,loading_shadow:'97% dark left -> clear right',pattern_alpha:'transparent left -> opaque right'},null,2));
 console.log('RENDERED',civ,rows.length,'UI surfaces','cover',cover.bytes);
}

