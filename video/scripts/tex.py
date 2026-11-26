import asyncio, json
from playwright.async_api import async_playwright
html=open('desktop.html').read().replace('DATA_JSON', open('data.json').read()); open('built.html','w').write(html)
OUT='/home/claude/workspace/video/tex/'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--font-render-hinting=none'])
        pg=await b.new_page(viewport={'width':1512,'height':982}, device_scale_factor=2)
        await pg.goto('file:///home/claude/vid/ui/built.html'); await pg.wait_for_timeout(400); await pg.evaluate('setTex()')
        await pg.evaluate('render(0)'); await pg.screenshot(path=OUT+'dash.jpg',type='jpeg',quality=90)
        for i in range(60):
            await pg.evaluate(f'render({17.5+i/30})'); await pg.screenshot(path=OUT+f'think_{i:03d}.jpg',type='jpeg',quality=85)
        r=await pg.evaluate("(()=>{const e=document.querySelector('#think span').getBoundingClientRect();return [e.left,e.top,e.width,e.height]})()")
        json.dump({'think_rect_px':r,'screen_px':[1512,982]},open(OUT+'think_rect.json','w')); print(r)
        await b.close()
asyncio.run(main())
