# animation-refs

مراجع أنيميشن (three.js + GSAP) مسحوبة بـ shallow clone (`--depth 1`) داخل هذا المجلد للرجوع إليها محلياً. لم يتم تنصيب أي dependencies.

> الريبوهات نفسها **غير مضافة** إلى git (مستثناة في `.gitignore`) — هذا الملف فقط هو المحفوظ. لإعادة سحبها:
>
> ```bash
> cd animation-refs
> git clone --depth 1 https://github.com/mrdoob/three.js
> git clone --depth 1 https://github.com/greensock/GSAP
> ```

## 1. three.js — `animation-refs/three.js`

مكتبة JavaScript للرسوميات ثلاثية الأبعاد في المتصفح (WebGL و WebGPU): مشاهد، كاميرات، إضاءة، مواد، shaders، أنظمة جزيئات، وأنيميشن.

- **الأمثلة:** `three.js/examples/*.html` — كل مثال صفحة HTML مستقلة (`webgl_*`، `webgpu_*`، `css3d_*`، `webxr_*`...).
- **الكود المساعد (addons):** `three.js/examples/jsm/` — مثلاً `jsm/objects/Water.js` و `Water2.js` و `WaterMesh.js` و `Sky.js` و `SkyMesh.js`، و `jsm/shaders/WaterRefractionShader.js`.
- **الأصول (textures/models):** `three.js/examples/textures/` و `three.js/examples/models/`.
- **نسخة أونلاين:** https://threejs.org/examples/

## 2. GSAP — `animation-refs/GSAP`

مكتبة GreenSock لأنيميشن الواجهات: tweens، timelines، وplugins مثل ScrollTrigger و Flip و MotionPath و SplitText و Draggable.

- **السورس:** `GSAP/src/` (مثلاً `gsap-core.js`، `ScrollTrigger.js`، `Flip.js`، `MotionPathPlugin.js`، `Physics2DPlugin.js`).
- **النسخ المبنية:** `GSAP/dist/` (UMD) و `GSAP/esm/` (ES modules)، والأنواع في `GSAP/types/`.
- **الأمثلة:** الريبو **لا يحتوي مجلد أمثلة**؛ الأمثلة والديموهات موجودة على https://gsap.com/demos و https://codepen.io/GreenSock

## أمثلة three.js: ماء، محيط، جزيئات، ضباب

القائمة مأخوذة من أسماء الملفات تحت `three.js/examples/`. المسارات نسبةً إلى جذر ريبو crypto-signals.

### الماء والمحيط (Water / Ocean / Sea)

| المثال | المسار الكامل |
|---|---|
| `webgl_gpgpu_water` | `animation-refs/three.js/examples/webgl_gpgpu_water.html` |
| `webgl_shaders_ocean` | `animation-refs/three.js/examples/webgl_shaders_ocean.html` |
| `webgpu_backdrop_water` | `animation-refs/three.js/examples/webgpu_backdrop_water.html` |
| `webgpu_compute_water` | `animation-refs/three.js/examples/webgpu_compute_water.html` |
| `webgpu_ocean` | `animation-refs/three.js/examples/webgpu_ocean.html` |
| `webgpu_tsl_raging_sea` | `animation-refs/three.js/examples/webgpu_tsl_raging_sea.html` |
| `webgpu_water` | `animation-refs/three.js/examples/webgpu_water.html` |
| `webgpu_volume_caustics` | `animation-refs/three.js/examples/webgpu_volume_caustics.html` |

### الجزيئات (Particles / Points / Sprites)

| المثال | المسار الكامل |
|---|---|
| `webgl_buffergeometry_custom_attributes_particles` | `animation-refs/three.js/examples/webgl_buffergeometry_custom_attributes_particles.html` |
| `webgl_buffergeometry_points` | `animation-refs/three.js/examples/webgl_buffergeometry_points.html` |
| `webgl_buffergeometry_points_interleaved` | `animation-refs/three.js/examples/webgl_buffergeometry_points_interleaved.html` |
| `webgl_custom_attributes_points` | `animation-refs/three.js/examples/webgl_custom_attributes_points.html` |
| `webgl_custom_attributes_points2` | `animation-refs/three.js/examples/webgl_custom_attributes_points2.html` |
| `webgl_custom_attributes_points3` | `animation-refs/three.js/examples/webgl_custom_attributes_points3.html` |
| `webgl_interactive_points` | `animation-refs/three.js/examples/webgl_interactive_points.html` |
| `webgl_interactive_raycasting_points` | `animation-refs/three.js/examples/webgl_interactive_raycasting_points.html` |
| `webgl_points_billboards` | `animation-refs/three.js/examples/webgl_points_billboards.html` |
| `webgl_points_dynamic` | `animation-refs/three.js/examples/webgl_points_dynamic.html` |
| `webgl_points_sprites` | `animation-refs/three.js/examples/webgl_points_sprites.html` |
| `webgl_points_waves` | `animation-refs/three.js/examples/webgl_points_waves.html` |
| `webgl_sprites` | `animation-refs/three.js/examples/webgl_sprites.html` |
| `webgpu_compute_particles` | `animation-refs/three.js/examples/webgpu_compute_particles.html` |
| `webgpu_compute_particles_fluid` | `animation-refs/three.js/examples/webgpu_compute_particles_fluid.html` |
| `webgpu_compute_particles_rain` | `animation-refs/three.js/examples/webgpu_compute_particles_rain.html` |
| `webgpu_compute_particles_snow` | `animation-refs/three.js/examples/webgpu_compute_particles_snow.html` |
| `webgpu_compute_points` | `animation-refs/three.js/examples/webgpu_compute_points.html` |
| `webgpu_instance_points` | `animation-refs/three.js/examples/webgpu_instance_points.html` |
| `webgpu_instance_sprites` | `animation-refs/three.js/examples/webgpu_instance_sprites.html` |
| `webgpu_particles` | `animation-refs/three.js/examples/webgpu_particles.html` |
| `webgpu_particles_soft` | `animation-refs/three.js/examples/webgpu_particles_soft.html` |
| `webgpu_skinning_points` | `animation-refs/three.js/examples/webgpu_skinning_points.html` |
| `webgpu_sprites` | `animation-refs/three.js/examples/webgpu_sprites.html` |
| `webgpu_tsl_compute_attractors_particles` | `animation-refs/three.js/examples/webgpu_tsl_compute_attractors_particles.html` |
| `webgpu_tsl_vfx_linkedparticles` | `animation-refs/three.js/examples/webgpu_tsl_vfx_linkedparticles.html` |
| `css3d_sprites` | `animation-refs/three.js/examples/css3d_sprites.html` |

### الضباب والحجم (Fog / Volumetric)

| المثال | المسار الكامل |
|---|---|
| `webgpu_custom_fog` | `animation-refs/three.js/examples/webgpu_custom_fog.html` |
| `webgpu_custom_fog_background` | `animation-refs/three.js/examples/webgpu_custom_fog_background.html` |
| `webgpu_custom_fog_scattering` | `animation-refs/three.js/examples/webgpu_custom_fog_scattering.html` |
| `webgpu_fog_height` | `animation-refs/three.js/examples/webgpu_fog_height.html` |
| `webgpu_postprocessing_fog` | `animation-refs/three.js/examples/webgpu_postprocessing_fog.html` |
| `webgl_volume_cloud` | `animation-refs/three.js/examples/webgl_volume_cloud.html` |
| `webgpu_volume_cloud` | `animation-refs/three.js/examples/webgpu_volume_cloud.html` |
| `webgl_volume_perlin` | `animation-refs/three.js/examples/webgl_volume_perlin.html` |
| `webgpu_volume_perlin` | `animation-refs/three.js/examples/webgpu_volume_perlin.html` |
| `webgpu_volume_lighting` | `animation-refs/three.js/examples/webgpu_volume_lighting.html` |
| `webgpu_volume_lighting_rectarea` | `animation-refs/three.js/examples/webgpu_volume_lighting_rectarea.html` |
| `webgpu_volume_lighting_traa` | `animation-refs/three.js/examples/webgpu_volume_lighting_traa.html` |
| `webgpu_volume_fire` | `animation-refs/three.js/examples/webgpu_volume_fire.html` |

### ملفات addons ذات صلة

| الملف | المسار الكامل |
|---|---|
| `Water.js` | `animation-refs/three.js/examples/jsm/objects/Water.js` |
| `Water2.js` | `animation-refs/three.js/examples/jsm/objects/Water2.js` |
| `WaterMesh.js` | `animation-refs/three.js/examples/jsm/objects/WaterMesh.js` |
| `Water2Mesh.js` | `animation-refs/three.js/examples/jsm/objects/Water2Mesh.js` |
| `Sky.js` | `animation-refs/three.js/examples/jsm/objects/Sky.js` |
| `SkyMesh.js` | `animation-refs/three.js/examples/jsm/objects/SkyMesh.js` |
| `WaterRefractionShader.js` | `animation-refs/three.js/examples/jsm/shaders/WaterRefractionShader.js` |
