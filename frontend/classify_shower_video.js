/**
* 视频分类页面组件
* 这是分类展示功能模块(classify_shower)的组件，不能独立作为组件使用。
*/

class CS_VideoWidget {
    constructor() {
        this.anime_svg_string = `<path fill-rule="evenodd" clip-rule="evenodd" d="M19.9068 9.24502C17.7722 7.18582 17.7722 3.76656 19.9068 1.70742C21.9355 -0.249681 25.1494 -0.249681 27.1782 1.70742L38.4919 12.6215C38.8133 12.9316 39.0863 13.2725 39.311 13.635H56.4208C56.6459 13.2725 56.9189 12.9316 57.24 12.6215L68.5536 1.70742C70.5824 -0.249681 73.7963 -0.249681 75.8251 1.70742C77.96 3.76656 77.96 7.18582 75.8251 9.24502L71.2747 13.635H74.6667C86.4485 13.635 96 23.1863 96 34.9684V64.3312C96 76.1131 86.4485 85.6645 74.6667 85.6645H21.3333C9.55125 85.6645 0 76.1131 0 64.3312V34.9683C0 23.1862 9.55125 13.635 21.3333 13.635H24.4575L19.9068 9.24502ZM21.3333 23.925C15.4423 23.925 10.6667 28.7006 10.6667 34.5916V64.7077C10.6667 70.5989 15.4423 75.3744 21.3333 75.3744H74.6667C80.5579 75.3744 85.3333 70.5989 85.3333 64.7077V34.5916C85.3333 28.7006 80.5579 23.925 74.6667 23.925H21.3333ZM26.6667 44.6932C26.6667 41.7477 29.0545 39.3598 32 39.3598C34.9455 39.3598 37.3333 41.7477 37.3333 44.6932V49.4613C37.3333 52.4069 34.9455 54.7947 32 54.7947C29.0545 54.7947 26.6667 52.4069 26.6667 49.4613V44.6932ZM64 39.3598C61.0544 39.3598 58.6667 41.7477 58.6667 44.6932V49.4613C58.6667 52.4069 61.0544 54.7947 64 54.7947C66.9456 54.7947 69.3333 52.4069 69.3333 49.4613V44.6932C69.3333 41.7477 66.9456 39.3598 64 39.3598Z" fill="#00AEEC"/>`;
        this.movie_svg_string = `<path d="M925.866667 177.066667L85.333333 320l-6.4-42.666667C70.4 230.4 102.4 187.733333 149.333333 179.2l674.133334-113.066667c46.933333-8.533333 89.6 23.466667 98.133333 70.4l4.266667 40.533334zM853.333333 874.666667H170.666667c-46.933333 0-85.333333-38.4-85.333334-85.333334V320h853.333334v469.333333c0 46.933333-38.4 85.333333-85.333334 85.333334z" fill="#3F51B5" /><path d="M401.066667 136.533333l104.533333 113.066667 85.333333-14.933333-106.666666-113.066667zM232.533333 164.266667l104.533334 113.066666 85.333333-14.933333-106.666667-110.933333zM569.6 108.8l104.533333 110.933333 83.2-12.8-104.533333-113.066666zM736 81.066667l106.666667 110.933333 83.2-14.933333-104.533334-110.933334z" fill="#9FA8DA" /><path d="M160 245.333333m-32 0a32 32 0 1 0 64 0 32 32 0 1 0-64 0Z" fill="#9FA8DA" /><path d="M853.333333 320l-85.333333 128h85.333333l85.333334-128zM682.666667 320l-85.333334 128h85.333334l85.333333-128zM512 320l-85.333333 128h85.333333l85.333333-128zM341.333333 320l-85.333333 128h85.333333l85.333334-128zM170.666667 320l-85.333334 128h85.333334l85.333333-128z" fill="#9FA8DA" />`;
        this.re_creation_svg_string = `<path d="M512 469.333333m-426.666667 0a426.666667 426.666667 0 1 0 853.333334 0 426.666667 426.666667 0 1 0-853.333334 0Z" fill="#FFF59D" /><path d="M789.333333 469.333333c0-164.266667-140.8-294.4-309.333333-275.2-128 14.933333-230.4 117.333333-243.2 245.333334-10.666667 98.133333 29.866667 185.6 98.133333 241.066666 29.866667 25.6 49.066667 61.866667 49.066667 102.4v6.4h256v-2.133333c0-38.4 17.066667-76.8 46.933333-102.4 61.866667-51.2 102.4-128 102.4-215.466667z" fill="#FBC02D" /><path d="M652.8 430.933333l-64-42.666666c-6.4-4.266667-17.066667-4.266667-23.466667 0L512 422.4l-51.2-34.133333c-6.4-4.266667-17.066667-4.266667-23.466667 0l-64 42.666666c-4.266667 4.266667-8.533333 8.533333-8.533333 14.933334s0 12.8 4.266667 17.066666l81.066666 100.266667V789.333333h42.666667V554.666667c0-4.266667-2.133333-8.533333-4.266667-12.8l-70.4-87.466667 32-21.333333 51.2 34.133333c6.4 4.266667 17.066667 4.266667 23.466667 0l51.2-34.133333 32 21.333333-70.4 87.466667c-2.133333 4.266667-4.266667 8.533333-4.266667 12.8v234.666666h42.666667V563.2l81.066667-100.266667c4.266667-4.266667 6.4-10.666667 4.266666-17.066666s-4.266667-12.8-8.533333-14.933334z" fill="#FFF59D" /><path d="M512 938.666667m-64 0a64 64 0 1 0 128 0 64 64 0 1 0-128 0Z" fill="#5C6BC0" /><path d="M554.666667 960h-85.333334c-46.933333 0-85.333333-38.4-85.333333-85.333333v-106.666667h256v106.666667c0 46.933333-38.4 85.333333-85.333333 85.333333z" fill="#9FA8DA" /><path d="M640 874.666667l-247.466667 34.133333c6.4 14.933333 19.2 29.866667 34.133334 38.4l200.533333-27.733333c8.533333-12.8 12.8-27.733333 12.8-44.8zM384 825.6v42.666667L640 832v-42.666667z" fill="#5C6BC0" />`;
        this.other_svg_string = `<path d="M768 938.666667H170.666667V170.666667h426.666666l170.666667 170.666666z" fill="#42A5F5" /><path d="M853.333333 853.333333H256V85.333333h426.666667l170.666666 170.666667z" fill="#90CAF9" /><path d="M821.333333 277.333333H661.333333V117.333333z" fill="#E1F5FE" /><path d="M522.666667 603.733333c0-100.266667 76.8-93.866667 76.8-153.6 0-14.933333-4.266667-44.8-42.666667-44.8-42.666667 0-44.8 34.133333-44.8 42.666667h-57.6c0-14.933333 6.4-89.6 102.4-89.6 98.133333 0 100.266667 76.8 100.266667 91.733333 0 74.666667-81.066667 85.333333-81.066667 155.733334h-53.333333z m-4.266667 74.666667c0-4.266667 0-32 32-32 29.866667 0 32 27.733333 32 32 0 8.533333-4.266667 29.866667-32 29.866667s-32-21.333333-32-29.866667z" fill="#1976D2" />`;
        this.film_svg_string = `<path d="M917.333333 832V512h-85.333333v320c0 106.666667 85.333333 192 192 192v-85.333333c-59.733333 0-106.666667-46.933333-106.666667-106.666667z" fill="#3F51B5" /><path d="M512 512m-405.333333 0a405.333333 405.333333 0 1 0 810.666666 0 405.333333 405.333333 0 1 0-810.666666 0Z" fill="#90A4AE" /><path d="M512 512m-42.666667 0a42.666667 42.666667 0 1 0 85.333334 0 42.666667 42.666667 0 1 0-85.333334 0Z" fill="#37474F" /><path d="M512 298.666667m-106.666667 0a106.666667 106.666667 0 1 0 213.333334 0 106.666667 106.666667 0 1 0-213.333334 0Z" fill="#253278" /><path d="M512 725.333333m-106.666667 0a106.666667 106.666667 0 1 0 213.333334 0 106.666667 106.666667 0 1 0-213.333334 0Z" fill="#253278" /><path d="M725.333333 512m-106.666666 0a106.666667 106.666667 0 1 0 213.333333 0 106.666667 106.666667 0 1 0-213.333333 0Z" fill="#253278" /><path d="M298.666667 512m-106.666667 0a106.666667 106.666667 0 1 0 213.333333 0 106.666667 106.666667 0 1 0-213.333333 0Z" fill="#253278" />`;
        this.teleplay_svg_string = `<path d="M896 832H128V490.666667L512 128l384 362.666667z" fill="#E8EAF6" /><path d="M832 448l-106.666667-106.666667V192h106.666667zM128 832h768v106.666667H128z" fill="#C5CAE9" /><path d="M512 91.733333L85.333333 488.533333l42.666667 46.933334L512 179.2l384 356.266667 42.666667-46.933334z" fill="#B71C1C" /><path d="M384 597.333333h256v341.333334H384z" fill="#D84315" /><path d="M448 362.666667h128v128h-128z" fill="#01579B" /><path d="M586.666667 757.333333c-6.4 0-10.666667 4.266667-10.666667 10.666667v42.666667c0 6.4 4.266667 10.666667 10.666667 10.666666s10.666667-4.266667 10.666666-10.666666v-42.666667c0-6.4-4.266667-10.666667-10.666666-10.666667z" fill="#FF8A65" />`;
        this.documentary_svg_string = `<path d="M132 48V96C132 98.274 130.716 100.35 128.682 101.37C127.836 101.79 126.912 102 126 102C124.728 102 123.456 101.598 122.4 100.8L102.504 85.878L114 132L43.5 108.432C22.878 102.186 12 72 12 72C12 72 22.878 42.72 43.5 35.778L114.114 12L102.552 58.086L122.4 43.2C124.218 41.838 126.648 41.616 128.682 42.63C130.716 43.65 132 45.726 132 48Z" fill="#FF8F00"/>
<path opacity="0.4" d="M102.54 58.08L114.12 12L72 26.16V33.24L97.14 30.36L86.64 72.36L97.074 113.7L72 110.82V117.966L114 132L102.48 85.86L102.54 58.08ZM48 109.92L63 114.96V109.8L48 108.06V109.92ZM48 36L63 34.26V29.22L48 34.26V36Z" fill="white"/>
<path opacity="0.3" d="M33 69C33 72.312 30.312 75 27 75C23.688 75 21 72.312 21 69C21 65.688 23.688 63 27 63C30.312 63 33 65.688 33 69ZM48 36V34.26L43.5 35.778C41.94 36.3 40.446 36.966 39 37.722V106.614C40.446 107.334 41.94 107.958 43.5 108.432L48 109.938V109.92V108.06V36ZM72 110.82V33.24V26.178L63 29.208V29.22V34.26V109.8V114.954L72 117.96V110.82ZM102.54 58.152L102.48 85.782L102.504 85.878L114 94.5V49.5L102.552 58.086L102.54 58.152Z" fill="#000000"/>`;
        this.streaming_media_svg_string = `<path d="M512 85.333333C277.333333 85.333333 85.333333 277.333333 85.333333 512s192 426.666667 426.666667 426.666667 426.666667-192 426.666667-426.666667S746.666667 85.333333 512 85.333333z" fill="#7CB342" />
<path d="M960 512c0 249.6-202.666667 448-448 448S64 761.6 64 512 262.4 64 512 64s448 198.4 448 448z m-452.266667 206.933333c0-8.533333-4.266667-12.8-12.8-17.066666-27.733333-8.533333-53.333333-8.533333-76.8-32-4.266667-8.533333-4.266667-17.066667-8.533333-27.733334-8.533333-8.533333-32-12.8-44.8-17.066666h-89.6c-12.8-4.266667-23.466667-23.466667-32-36.266667 0-4.266667 0-12.8-8.533333-12.8-8.533333-4.266667-17.066667 4.266667-27.733334 0-4.266667-4.266667-4.266667-8.533333-4.266666-12.8 0-12.8 8.533333-27.733333 17.066666-36.266667 12.8-8.533333 27.733333 4.266667 40.533334 4.266667 4.266667 0 4.266667 0 8.533333 4.266667 12.8 4.266667 17.066667 21.333333 17.066667 36.266666v8.533334c0 4.266667 4.266667 4.266667 8.533333 4.266666 4.266667-23.466667 4.266667-44.8 8.533333-68.266666 0-27.733333 27.733333-53.333333 49.066667-61.866667 8.533333-4.266667 12.8 4.266667 23.466667 0 27.733333-8.533333 93.866667-36.266667 81.066666-72.533333-8.533333-32-36.266667-61.866667-72.533333-57.6-8.533333 4.266667-12.8 8.533333-21.333333 12.8-12.8 8.533333-40.533333 36.266667-53.333334 36.266666-23.466667-4.266667-23.466667-36.266667-17.066666-49.066666 4.266667-17.066667 44.8-76.8 72.533333-66.133334l17.066667 17.066667c8.533333 4.266667 23.466667 4.266667 36.266666 4.266667 4.266667 0 8.533333 0 12.8-4.266667 4.266667-4.266667 4.266667-4.266667 4.266667-8.533333 0-12.8-12.8-27.733333-21.333333-36.266667-8.533333-8.533333-23.466667-17.066667-36.266667-23.466667-44.8-12.8-117.333333 4.266667-151.466667 36.266667s-61.866667 85.333333-81.066666 130.133333c-8.533333 27.733333-17.066667 61.866667-21.333334 93.866667-4.266667 21.333333-8.533333 40.533333 4.266667 61.866667 12.8 27.733333
 40.533333 53.333333 68.266667 72.533333 17.066667 12.8 53.333333 12.8 72.533333 36.266667 12.8 17.066667 8.533333 40.533333 8.533333 61.866666 0 27.733333 17.066667 49.066667 27.733334 72.533334 4.266667 12.8 8.533333 32 12.8 44.8 0 4.266667 4.266667 32 4.266666 36.266666 27.733333 12.8 49.066667 27.733333 81.066667 36.266667 4.266667 0 21.333333-27.733333 21.333333-32 12.8-12.8 23.466667-32 36.266667-40.533333 8.533333-4.266667 17.066667-8.533333 27.733333-17.066667 8.533333-8.533333 12.8-27.733333 17.066667-40.533333 2.133333-10.666667 6.4-27.733333 2.133333-40.533334z m8.533334-413.866666c4.266667 0 8.533333-4.266667 17.066666-8.533334 12.8-8.533333 27.733333-23.466667 40.533334-32 12.8-8.533333 27.733333-23.466667 36.266666-32 12.8-8.533333 23.466667-27.733333 27.733334-40.533333 4.266667-8.533333 17.066667-27.733333 12.8-40.533333-4.266667-8.533333-27.733333-12.8-36.266667-17.066667-36.266667-8.533333-66.133333-12.8-102.4-12.8-12.8 0-32 4.266667-36.266667 17.066667-4.266667 23.466667 12.8 17.066667 32 23.466666 0 0 4.266667 36.266667 4.266667 40.533334 4.266667 21.333333-8.533333 36.266667-8.533333 57.6 0 12.8 0 36.266667 8.533333 44.8h4.266667zM891.733333 618.666667c4.266667-8.533333 4.266667-23.466667 8.533334-32 4.266667-21.333333 4.266667-44.8 4.266666-66.133334 0-44.8-4.266667-89.6-17.066666-130.133333-8.533333-12.8-12.8-27.733333-17.066667-40.533333-8.533333-23.466667-21.333333-44.8-40.533333-61.866667-17.066667-23.466667-40.533333-85.333333-81.066667-66.133333-12.8 4.266667-21.333333 21.333333-32 32-8.533333 12.8-17.066667 27.733333-27.733333 40.533333-4.266667 4.266667-8.533333 12.8-4.266667 17.066667 0 4.266667 4.266667 4.266667 8.533333 4.266666 8.533333 
 4.266667 12.8 4.266667 21.333334 8.533334 4.266667 0 8.533333 4.266667 4.266666 8.533333 0 0 0 4.266667-4.266666 4.266667-21.333333 23.466667-44.8 40.533333-66.133334 61.866666-4.266667 4.266667-8.533333 12.8-8.533333 17.066667 0 4.266667 4.266667 4.266667 4.266667 8.533333s-4.266667 4.266667-8.533334 8.533334c-8.533333 4.266667-17.066667 8.533333-23.466666 12.8-4.266667 8.533333 0 23.466667-4.266667 32-4.266667 23.466667-17.066667 40.533333-27.733333 61.866666-8.533333 12.8-12.8 27.733333-21.333334 40.533334 0 17.066667-4.266667 32 4.266667 44.8 21.333333 32 61.866667 12.8 93.866667 27.733333 8.533333 4.266667 17.066667 4.266667 23.466666 12.8 12.8 12.8 12.8 36.266667 17.066667 49.066667 4.266667 17.066667 8.533333 36.266667 17.066667 53.333333 4.266667 21.333333 12.8 44.8 17.066666 61.866667 40.533333-32 76.8-66.133333 102.4-110.933334 32-27.733333 44.8-64 57.6-100.266666z" fill="#0277BD" />`;
        this.photo_svg_string = `<path d="M213.333333 192c-46.933333 0-85.333333 38.4-85.333333 85.333333v554.666667c0 46.933333 38.4 85.333333 85.333333 85.333333h341.333334c46.933333 0 85.333333-38.4 85.333333-85.333333V277.333333c0-46.933333-38.4-85.333333-85.333333-85.333333" fill="#673AB7" /><path d="M298.666667 277.333333h42.666666v554.666667h-42.666666zM512 192V149.333333c0-25.6-17.066667-42.666667-42.666667-42.666666h-170.666666c-25.6 0-42.666667 17.066667-42.666667 42.666666v42.666667h256z" fill="#311B92" /><path d="M640 277.333333H341.333333v554.666667h298.666667V277.333333z m-192 512h-64v-85.333333h64v85.333333z m0-384h-64v-85.333333h64v85.333333z m128 384h-64v-85.333333h64v85.333333z m-64-384v-85.333333h64v85.333333h-64z" fill="#D84315" /><path d="M640 277.333333v42.666667h64v85.333333h-64v298.666667h64v85.333333h-64v42.666667h256V277.333333H640z m192 512h-64v-85.333333h64v85.333333z m0-384h-64v-85.333333h64v85.333333z" fill="#FF5722" />`;
        this.adult_anime_svg_string = `
<g>
	<path style="fill:#CC3333;" d="M64,4C30.86,4,4,30.86,4,64s26.86,60,60,60s60-26.86,60-60S97.14,4,64,4z M114,64
		c0.04,11.53-3.96,22.71-11.3,31.6L32.4,25.3C41.29,17.96,52.47,13.96,64,14C91.61,14,114,36.39,114,64z M14,64
		c-0.04-11.53,3.96-22.71,11.3-31.6l70.3,70.3c-8.89,7.34-20.07,11.34-31.6,11.3C36.39,114,14,91.61,14,64z"/>
	<circle style="fill:#F44336;" cx="60.1" cy="63.1" r="56.1"/>
	<path style="fill:#FFFFFF;" d="M95.6,102.7c-8.89,7.34-20.07,11.34-31.6,11.3c-27.61,0-50-22.39-50-50
		c-0.04-11.53,3.96-22.71,11.3-31.6l7.1-7.1C41.29,17.96,52.47,13.96,64,14c27.61,0,50,22.39,50,50c0.04,11.53-3.96,22.71-11.3,31.6
		"/>
	<path style="fill:#231F20;" d="M95.6,102.7c-8.89,7.34-20.07,11.34-31.6,11.3c-27.61,0-50-22.39-50-50
		c-0.04-11.53,3.96-22.71,11.3-31.6l7.1-7.1C41.29,17.96,52.47,13.96,64,14c27.61,0,50,22.39,50,50c0.04,11.53-3.96,22.71-11.3,31.6
		"/>
	<path style="fill:#414042;" d="M96.4,103.2c-20.49,16.74-50.66,13.7-67.4-6.79C14.59,78.78,14.59,53.44,29,35.8l6.8-6.8
		c8.53-7.03,19.25-10.85,30.3-10.8c26.45,0,47.9,21.44,47.9,47.9c0,11.04-3.82,21.75-10.8,30.3"/>
	<path style="fill:#FAFAFA;" d="M93,58.3c0.04,2.74-0.77,5.43-2.3,7.7c-1.55,2.29-3.69,4.13-6.2,5.3c2.88,1.2,5.37,3.18,7.2,5.7
		c1.79,2.47,2.74,5.45,2.7,8.5c0.19,4.56-1.68,8.97-5.1,12c-3.4,3-7.9,4.5-13.4,4.5s-10.1-1.5-13.4-4.5c-3.42-3.03-5.29-7.44-5.1-12
		c-0.01-3.03,0.89-5.99,2.6-8.5c1.79-2.55,4.25-4.55,7.1-5.8c-2.48-1.18-4.59-3.01-6.1-5.3c-1.49-2.29-2.26-4.97-2.2-7.7
		c0-4.9,1.6-8.8,4.7-11.7c3.1-2.9,7.3-4.3,12.4-4.3s9.2,1.4,12.4,4.3C91.46,49.59,93.17,53.88,93,58.3z M86.9,85.4
		c0.13-2.98-1-5.88-3.1-8c-2.18-2.07-5.1-3.18-8.1-3.1c-5.69-0.39-10.61,3.91-11,9.59c-0.03,0.47-0.03,0.94,0,1.41
		c-0.14,2.89,0.91,5.71,2.9,7.8c1.9,1.9,4.7,2.8,8.2,2.8S82,95,83.9,93C85.9,91.3,86.9,88.7,86.9,85.4z M75.8,48.4
		c-2.61-0.13-5.15,0.85-7,2.7c-1.87,1.96-2.85,4.6-2.7,7.3c-0.11,2.67,0.87,5.26,2.7,7.2c1.89,1.85,4.46,2.83,7.1,2.7
		c2.64,0.13,5.21-0.85,7.1-2.7c1.85-1.93,2.83-4.53,2.7-7.2c0.14-2.69-0.88-5.31-2.8-7.2C80.99,49.37,78.44,48.36,75.8,48.4z"/>
	<path style="fill:#FAFAFA;" d="M49.1,43l-14.3,5.4c-0.68,0.23-1.13,0.88-1.1,1.6v3.2c0,0.94,0.77,1.71,1.71,1.71
		c0.2,0,0.4-0.04,0.59-0.11l4.9-1.8c0.89-0.33,1.87,0.13,2.19,1.01c0.07,0.19,0.1,0.39,0.11,0.59v45.1c0.03,0.93,0.77,1.67,1.7,1.7
		H49c0.93-0.03,1.67-0.77,1.7-1.7V44.1c0-0.67-0.55-1.22-1.23-1.21c-0.06,0-0.12,0-0.17,0.01L49.1,43z"/>
	<path style="fill:#FAFAFA;" d="M84.6,34.7h-1.1c-0.38-0.01-0.69,0.28-0.7,0.66c0,0.01,0,0.03,0,0.04v3
		c0.01,0.38-0.28,0.69-0.66,0.7c-0.01,0-0.03,0-0.04,0h-0.5c-0.38,0.01-0.69-0.28-0.7-0.66c0-0.01,0-0.03,0-0.04V28.3
		c-0.01-0.38,0.28-0.69,0.66-0.7c0.01,0,0.03,0,0.04,0h3.3c1.11-0.07,2.2,0.25,3.1,0.9c0.74,0.66,1.14,1.61,1.1,2.6
		c0.02,0.71-0.19,1.41-0.6,2c-0.26,0.38-0.6,0.68-1,0.9c-0.3,0.24-0.42,0.64-0.3,1l2.3,4.2v0.1h-1.7c-0.28-0.03-0.53-0.17-0.7-0.4
		l-1.9-3.7C85.1,34.8,84.9,34.7,84.6,34.7z M82.8,32.3c-0.01,0.38,0.28,0.69,0.66,0.7c0.01,0,0.03,0,0.04,0h1.3
		c0.57,0.02,1.14-0.16,1.6-0.5c0.41-0.34,0.64-0.86,0.6-1.4c0.02-0.51-0.16-1.01-0.5-1.4c-0.46-0.34-1.03-0.52-1.6-0.5h-1.4
		c-0.38-0.01-0.69,0.28-0.7,0.66c0,0.01,0,0.03,0,0.04L82.8,32.3z"/>
	<path style="fill:#FAFAFA;" d="M77.3,34h-3.9c-0.21,0.01-0.39,0.19-0.4,0.4v2.7c0.01,0.21,0.19,0.39,0.4,0.4H78
		c0.21,0.01,0.39,0.19,0.4,0.4v0.8c-0.01,0.21-0.19,0.39-0.4,0.4h-6.6c-0.21-0.01-0.39-0.19-0.4-0.4V28.1
		c0.01-0.21,0.19-0.39,0.4-0.4H78c0.21,0.01,0.39,0.19,0.4,0.4v0.8c-0.01,0.21-0.19,0.39-0.4,0.4h-4.6c-0.21,0.01-0.39,0.19-0.4,0.4
		V32c0.01,0.21,0.19,0.39,0.4,0.4h3.9c0.21,0.01,0.39,0.19,0.4,0.4v0.8c0.02,0.2-0.13,0.38-0.34,0.4C77.34,34,77.32,34,77.3,34z"/>
	<path style="fill:#FAFAFA;" d="M60.5,38.7V28.1c0.01-0.21,0.19-0.39,0.4-0.4h2.9c0.95-0.03,1.88,0.22,2.7,0.7
		c0.79,0.42,1.42,1.09,1.8,1.9c0.41,0.88,0.61,1.83,0.6,2.8v0.6c0.03,0.97-0.18,1.93-0.6,2.8c-0.41,0.79-1.03,1.45-1.8,1.9
		c-0.83,0.44-1.76,0.68-2.7,0.7h-2.9C60.69,39.09,60.51,38.91,60.5,38.7z M62.5,29.7v7.4c0.01,0.21,0.19,0.39,0.4,0.4h0.9
		c0.91,0.05,1.79-0.32,2.4-1c0.62-0.8,0.9-1.8,0.8-2.8v-0.6c0.05-1-0.23-1.98-0.8-2.8c-0.58-0.66-1.42-1.03-2.3-1h-1
		C62.69,29.31,62.51,29.49,62.5,29.7z"/>
	<path style="fill:#FAFAFA;" d="M46.5,27.7c0.21,0.01,0.39,0.19,0.4,0.4v7.2c0.05,1.1-0.39,2.16-1.2,2.9
		c-0.86,0.74-1.96,1.14-3.1,1.1c-1.12,0.07-2.23-0.29-3.1-1c-0.78-0.75-1.19-1.82-1.1-2.9v-7.2c0.01-0.21,0.19-0.39,0.4-0.4H40
		c0.21,0.01,0.39,0.19,0.4,0.4v7.2c-0.05,0.63,0.17,1.25,0.6,1.7c0.46,0.42,1.08,0.63,1.7,0.6c1.15,0.13,2.18-0.69,2.31-1.84
		c0.02-0.19,0.02-0.37-0.01-0.56v-7.1c0.01-0.21,0.19-0.39,0.4-0.4C45.4,27.7,46.5,27.7,46.5,27.7z"/>
	<path style="fill:#FAFAFA;" d="M57.5,39.1h-1.3c-0.1,0-0.3-0.1-0.3-0.2l-4.2-6.7c-0.2-0.3-0.8-0.2-0.8,0.2v6.2
		c-0.01,0.21-0.19,0.39-0.4,0.4h-1.2c-0.21-0.01-0.39-0.19-0.4-0.4V28.1c0.01-0.21,0.19-0.39,0.4-0.4h1.3c0.1,0,0.3,0.1,0.3,0.2
		l4.2,6.7c0.2,0.3,0.8,0.2,0.8-0.2v-6.3c0.01-0.21,0.19-0.39,0.4-0.4h1.1c0.21,0.01,0.39,0.19,0.4,0.4v10.5
		c0.08,0.17,0.01,0.38-0.17,0.47C57.59,39.09,57.55,39.1,57.5,39.1z"/>
	<polyline style="opacity:0.8;fill:#231F20;enable-background:new    ;" points="23.4,35.6 95,102.1 97,100.2 30.6,33.4 	"/>
	<path style="fill:#F44336;" d="M103.9,96.8L25.3,18.9L18.2,26l78.6,77.9"/>
	<path style="fill:#FF8A80;" d="M45,10.9c1.7-0.4,4.2-1.6,5.9-1.1c1.09,0.3,1.75,1.4,1.5,2.5c-0.37,0.81-1.12,1.37-2,1.5
		c-3.9,0.97-7.68,2.35-11.3,4.1c-7.18,3.78-13.38,9.19-18.1,15.8c-1.9,2.7-3.4,5.5-5.8,7.8c-0.21,0.23-0.49,0.37-0.8,0.4
		c-0.17,0.03-0.35-0.01-0.5-0.1c-1.2-0.5-1.4-1.1-1.2-2.3c0.18-1.01,0.52-1.99,1-2.9c1.01-1.76,2.11-3.46,3.3-5.1
		c1.89-2.91,4.11-5.59,6.6-8C30.4,17.2,39.2,12.4,45,10.9z"/>
	<polygon style="fill:#CC3333;" points="32.4,25.3 30.4,27.3 101.5,98.4 103.3,96.2 	"/>
</g>
`;
        this.videoCategories = {
            "二次元相关": [
                { name: "番剧", icon: this.anime_svg_string, description: "各种动画番剧" , viewbox: "0 0 96 86"},
                { name: "动漫二创", icon: this.re_creation_svg_string, description: "动漫相关的二次创作", viewbox: "64 64 960 960" },
                { name: "动漫电影", icon: this.movie_svg_string, description: "动漫电影作品", viewbox: "64 64 960 960" }
            ],
            "大众分类": [
                { name: "电影", icon: this.film_svg_string, description: "各类电影", viewbox: "0 0 1024 1024" },
                { name: "电视剧", icon: this.teleplay_svg_string, description: "各类电视剧", viewbox: "0 0 1024 1024" },
                { name: "纪录片", icon: this.documentary_svg_string, description: "各类纪录片", viewbox: "0 0 144 144" }
            ],
            "其他": [
                { name: "流媒体视频", icon: this.streaming_media_svg_string, description: "流媒体视频", viewbox: "64 64 960 960" },
                { name: "相册", icon: this.photo_svg_string, description: "视频相册", viewbox: "64 64 960 960" },
                { name:"还未分类", icon: this.other_svg_string, description: "未分类的视频", viewbox: "64 64 960 960" }
            ],
            "限制级": [
                { name: "里番", icon: this.adult_anime_svg_string, description: "成人向动画" , viewbox: "0 0 128 128"},
                { name: "限制级影视", icon: this.adult_anime_svg_string, description: "限制级影视作品", viewbox: "0 0 128 128" }
            ]
        };

    }

    /**
    * 绘制视频分类页面
    * @param {HTMLElement} container - 容器元素
    */
    render(container) {
        // 清空容器
        container.innerHTML = '';
        
        // 设置容器样式
        container.style.position = 'relative';
        container.style.height = '100%';
        container.style.overflow = 'hidden';
        
        // 在新页面右上角添加返回菜单栏
        const menuBar = document.createElement('div');
        menuBar.style.position = 'absolute';
        menuBar.style.top = '10px';
        menuBar.style.right = '20px';
        menuBar.style.display = 'flex';
        menuBar.style.gap = '10px';
        menuBar.style.zIndex = '100';
        menuBar.style.padding = '8px 12px';
        menuBar.style.background = 'rgba(200, 220, 255, 0.9)';
        menuBar.style.borderRadius = '20px';
        menuBar.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        
        const createIconButton = (svgString, onClick, viewbox_str) => {
            const btn = document.createElement('button');
            btn.style.cssText = 'width:40px;height:40px;border:none;border-radius:50%;background:#4A90D9;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;';
            btn.innerHTML = `<svg viewBox="${viewbox_str}" width="30" height="30" fill="white">${svgString}</svg>`;
            btn.onmouseover = () => { btn.style.background = '#357ABD'; btn.style.transform = 'scale(1.05)'; };
            btn.onmouseout = () => { btn.style.background = '#4A90D9'; btn.style.transform = 'scale(1)'; };
            btn.onclick = onClick;
            return btn;
        };
        
        const backBtn = createIconButton(cs_return_svg_string, (e) => { e.stopPropagation(); pop_page(1); }, cs_returnicon_viewbox);
        const rootBtn = createIconButton(cs_home_svg_string, (e) => { e.stopPropagation(); pop_page(256); }, cs_homeicon_viewbox);
        
        menuBar.appendChild(backBtn);
        menuBar.appendChild(rootBtn);
        container.appendChild(menuBar);
        
        // 创建滚动容器
        const scrollContainer = document.createElement('div');
        scrollContainer.style.display = 'flex';
        scrollContainer.style.flexDirection = 'column';
        scrollContainer.style.padding = '20px';
        scrollContainer.style.gap = '20px';
        scrollContainer.style.height = '100%';
        scrollContainer.style.overflowY = 'auto';
        scrollContainer.style.boxSizing = 'border-box';
        
        // 添加滚动条美化样式
        const scrollbarStyleId = `cs_scrollbar_style_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const scrollbarStyle = document.createElement('style');
        scrollbarStyle.id = scrollbarStyleId;
        scrollbarStyle.textContent = `
            .cs-player-scroll::-webkit-scrollbar {
                width: 8px;
            }
            .cs-player-scroll::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
            .cs-player-scroll::-webkit-scrollbar-thumb {
                background: linear-gradient(180deg, #4a90d9, #6ab0ff);
                border-radius: 4px;
            }
            .cs-player-scroll::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(180deg, #6ab0ff, #4a90d9);
            }
            .cs-player-scroll.hide-scrollbar::-webkit-scrollbar {
                width: 0;
            }
            .cs-player-scroll.hide-scrollbar::-webkit-scrollbar-thumb {
                background: transparent;
            }
        `;
        document.head.appendChild(scrollbarStyle);
        
        // 添加滚动条美化类
        scrollContainer.classList.add('cs-player-scroll');
        const scrollbarWidth = 8;
        scrollContainer.style.paddingRight = `${scrollbarWidth}px`;
        scrollContainer.classList.add('hide-scrollbar');
        
        // 滚动条自动隐藏逻辑
        let hideScrollbarTimer = null;
        const hideDelay = 2000;
        
        const showScrollbar = () => {
            if (scrollContainer.classList.contains('hide-scrollbar')) {
                scrollContainer.classList.remove('hide-scrollbar');
                scrollContainer.style.paddingRight = '0';
            }
            if (hideScrollbarTimer) {
                clearTimeout(hideScrollbarTimer);
            }
            hideScrollbarTimer = setTimeout(() => {
                scrollContainer.classList.add('hide-scrollbar');
                scrollContainer.style.paddingRight = `${scrollbarWidth}px`;
            }, hideDelay);
        };
        
        scrollContainer.addEventListener('scroll', showScrollbar);
        scrollContainer.addEventListener('mouseenter', showScrollbar);
        
        // 遍历中板块
        Object.entries(this.videoCategories).forEach(([categoryName, subCategories]) => {
            // 创建中板块容器
            const categoryContainer = document.createElement('div');
            categoryContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.35)';
            categoryContainer.style.borderRadius = '8px';
            categoryContainer.style.padding = '15px';
            categoryContainer.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            categoryContainer.style.marginRight = '15px';
            
            // 创建中板块标题
            const categoryTitle = document.createElement('h3');
            categoryTitle.textContent = categoryName;
            categoryTitle.style.marginTop = '0';
            categoryTitle.style.marginBottom = '15px';
            categoryTitle.style.color = '#333';
            categoryTitle.style.fontSize = '16px';
            categoryContainer.appendChild(categoryTitle);
            
            // 创建小版块容器
            const subCategoryContainer = document.createElement('div');
            subCategoryContainer.style.display = 'flex';
            subCategoryContainer.style.flexWrap = 'wrap';
            subCategoryContainer.style.gap = '15px';
            
            // 遍历小版块
            subCategories.forEach(subCategory => {
                // 创建小版块元素
                const subCategoryItem = document.createElement('div');
                subCategoryItem.style.display = 'flex';
                subCategoryItem.style.flexDirection = 'column';
                subCategoryItem.style.alignItems = 'center';
                subCategoryItem.style.padding = '15px';
                subCategoryItem.style.width = '120px';
                subCategoryItem.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                subCategoryItem.style.borderRadius = '8px';
                subCategoryItem.style.cursor = 'pointer';
                subCategoryItem.style.transition = 'all 0.3s ease';
                
                // 鼠标悬停效果
                subCategoryItem.addEventListener('mouseover', function() {
                    this.style.backgroundColor = '#ffffff';
                    this.style.transform = 'translateY(-2px)';
                });
                
                subCategoryItem.addEventListener('mouseout', function() {
                    this.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    this.style.transform = 'translateY(0)';
                });
                
                // 添加点击事件
                subCategoryItem.addEventListener('click', this.handleSubCategoryClick.bind(this, subCategory));
                
                // 创建图标
                const iconContainer = document.createElement('div');
                iconContainer.style.marginBottom = '10px';
                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.setAttribute('width', '48');
                svg.setAttribute('height', '48');
                svg.setAttribute('viewBox', subCategory.viewbox);
                svg.innerHTML = subCategory.icon;
                iconContainer.appendChild(svg);
                
                // 创建名称
                const nameContainer = document.createElement('div');
                nameContainer.style.fontSize = '14px';
                nameContainer.style.fontWeight = 'bold';
                nameContainer.style.textAlign = 'center';
                nameContainer.style.color = '#333';
                nameContainer.textContent = subCategory.name;
                
                // 创建描述
                const descriptionContainer = document.createElement('div');
                descriptionContainer.style.fontSize = '12px';
                descriptionContainer.style.textAlign = 'center';
                descriptionContainer.style.color = '#666';
                descriptionContainer.style.marginTop = '5px';
                descriptionContainer.textContent = subCategory.description;
                
                // 组装
                subCategoryItem.appendChild(iconContainer);
                subCategoryItem.appendChild(nameContainer);
                subCategoryItem.appendChild(descriptionContainer);
                subCategoryContainer.appendChild(subCategoryItem);
            });
            
            categoryContainer.appendChild(subCategoryContainer);
            scrollContainer.appendChild(categoryContainer);
        });
        
        // 将滚动容器添加到页面容器
        container.appendChild(scrollContainer);
        
        // 添加清理函数
        if (container.cleanFuncList) {
            container.cleanFuncList.push(() => {
                const styleToRemove = document.getElementById(scrollbarStyleId);
                if (styleToRemove) {
                    styleToRemove.parentNode.removeChild(styleToRemove);
                }
            });
        }
    }

    /**
    * 处理小版块点击事件
    * @param {Object} subCategory - 小版块数据
    */
    handleSubCategoryClick(subCategory) {
        console.log('点击了小版块:', subCategory.name);
        if (subCategory.name === '番剧') {
            const newPage = new_page();
            const animeWidget = new CS_AnimeWidget();
            animeWidget.render(newPage);
        }
    }
}

// 导出VideoWidget类
window.CS_VideoWidget = CS_VideoWidget;

/**
* 番剧页面组件
*/
class CS_AnimeWidget {
    constructor() {
        this.currentPage = 1;
        this.totalPages = 1;
        this.pageSize = 10;
        this.totalAnime = 0;
        this.sortBy = 'year';
        this.tagFilterEnabled = false;
        this.selectedTags = [];
        this.allTags = [];
        this.selectionMode = 'positive';
        this.pendingCallback = null;
        this.messageHandler = null;
    }

    async render(container) {
        container.innerHTML = '';
        container.style.display = 'flex';
        container.style.flexDirection = 'row';
        container.style.height = '100%';
        container.style.overflow = 'hidden';

        this.container = container;
        this.createBackButtons(container);
        await this.createSidebar(container);
        await this.createMainDisplay(container);
        this.registerMessageHandler();
        await this.fetchAnimeData();
    }

    registerMessageHandler() {
        this.messageHandler = (data) => {
            if (data.command === 'ANIME_PAGE_DATA' && data.widgetId === this.widgetId) {
                this.handleAnimePageData(data);
            } else if (data.command === 'ANIME_ALL_TAGS' && data.widgetId === this.widgetId) {
                this.handleAllTags(data);
            } else if (data.command === 'DATABASE_REBUILD_COMPLETE' && data.widgetId === this.widgetId) {
                this.currentPage = 1;
                this.fetchAnimeData();
            }
        };
        if (typeof message_proc_func_list !== 'undefined') {
            message_proc_func_list.push(this.messageHandler);
        }

        if (this.container.cleanFuncList) {
            this.container.cleanFuncList.push(() => {
                const idx = message_proc_func_list ? message_proc_func_list.indexOf(this.messageHandler) : -1;
                if (idx !== -1) message_proc_func_list.splice(idx, 1);
            });
        }
    }

    handleAnimePageData(data) {
        this.totalAnime = data.total;
        this.totalPages = Math.ceil(this.totalAnime / this.pageSize) || 1;
        this.allTags = data.allTags || [];
        this.renderPosters(data.animeList);
        this.renderPagination();
    }

    handleAllTags(data) {
        this.allTags = data.tags || [];
    }

    sendCommand(command, data = {}) {
        if (socket && socket.isConnected()) {
            socket.send(JSON.stringify({
                command: command,
                widgetId: this.widgetId,
                ...data
            }));
        }
    }

    createBackButtons(container) {
        this.widgetId = 'anime_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        cs_createBackButtons(container);
    }

    async createSidebar(container) {
        const sidebar = document.createElement('div');
        sidebar.style.cssText = 'width:28%;min-width:200px;height:100%;background:rgba(214, 228, 248, 0.7);padding:20px;display:flex;flex-direction:column;gap:20px;box-sizing:border-box;overflow-y:auto;border-right:1px solid #ccc;';
        sidebar.style.position = 'relative';
        sidebar.style.zIndex = '1';

        const sortRow = document.createElement('div');
        sortRow.style.cssText = 'display:flex;align-items:center;gap:10px;flex-wrap:wrap;';
        const sortLabel = document.createElement('div');
        sortLabel.style.cssText = 'font-size:14px;font-weight:bold;color:#333;white-space:nowrap;';
        sortLabel.textContent = '排序方式';
        const sortSelect = document.createElement('select');
        sortSelect.style.cssText = 'flex:1;padding:8px;border:1px solid #ccc;border-radius:4px;font-size:13px;min-width:0;';
        sortSelect.innerHTML = '<option value="year">按年份</option><option value="addtime">按入库时间</option><option value="pinyin">按拼音首字母</option>';
        sortSelect.value = this.sortBy;
        sortSelect.onchange = async () => {
            this.sortBy = sortSelect.value;
            this.currentPage = 1;
            await this.fetchAnimeData();
        };
        
        const orderToggle = document.createElement('label');
        orderToggle.style.cssText = 'display:flex;align-items:center;cursor:pointer;white-space:nowrap;';
        const orderCheckbox = document.createElement('input');
        orderCheckbox.type = 'checkbox';
        orderCheckbox.style.display = 'none';
        const orderSlider = document.createElement('div');
        orderSlider.style.cssText = 'position:relative;width:50px;height:24px;background:#ccc;border-radius:12px;transition:background 0.3s;';
        const orderKnob = document.createElement('div');
        orderKnob.style.cssText = 'position:absolute;top:2px;left:2px;width:20px;height:20px;background:#fff;border-radius:50%;transition:transform 0.3s;box-shadow:0 1px 3px rgba(0,0,0,0.3);';
        orderSlider.appendChild(orderKnob);
        const orderText = document.createElement('span');
        orderText.style.cssText = 'margin-left:8px;font-size:13px;color:#333;';
        orderText.textContent = '逆序';
        orderToggle.appendChild(orderCheckbox);
        orderToggle.appendChild(orderSlider);
        orderToggle.appendChild(orderText);
        this.sortOrder = 'DESC';
        orderCheckbox.checked = false;
        orderToggle.onclick = () => {
            orderCheckbox.checked = !orderCheckbox.checked;
            if (orderCheckbox.checked) {
                orderSlider.style.background = '#4CAF50';
                orderKnob.style.transform = 'translateX(26px)';
                orderText.textContent = '正序';
                this.sortOrder = 'ASC';
            } else {
                orderSlider.style.background = '#ccc';
                orderKnob.style.transform = 'translateX(0)';
                orderText.textContent = '逆序';
                this.sortOrder = 'DESC';
            }
            this.currentPage = 1;
            this.fetchAnimeData();
        };
        
        sortRow.appendChild(sortLabel);
        sortRow.appendChild(sortSelect);
        sortRow.appendChild(orderToggle);
        sidebar.appendChild(sortRow);

        const filterRow = document.createElement('div');
        filterRow.style.cssText = 'display:flex;align-items:center;gap:10px;margin-top:10px;';
        const filterLabel = document.createElement('div');
        filterLabel.style.cssText = 'font-size:14px;font-weight:bold;color:#333;white-space:nowrap;';
        filterLabel.textContent = '按标签筛选';
        const filterCheckbox = document.createElement('input');
        filterCheckbox.type = 'checkbox';
        filterCheckbox.id = 'tagFilterCheckbox';
        const filterLabel2 = document.createElement('label');
        filterLabel2.htmlFor = 'tagFilterCheckbox';
        filterLabel2.style.cssText = 'font-size:13px;cursor:pointer;white-space:nowrap;';
        filterLabel2.textContent = '启用标签筛选';
        filterRow.appendChild(filterLabel);
        filterRow.appendChild(filterCheckbox);
        filterRow.appendChild(filterLabel2);
        sidebar.appendChild(filterRow);

        const tagInputRow = document.createElement('div');
        tagInputRow.style.cssText = 'display:flex;gap:0;margin-bottom:10px;';
        this.tagInput = document.createElement('input');
        this.tagInput.type = 'text';
        this.tagInput.placeholder = '已选标签';
        this.tagInput.readOnly = true;
        this.tagInput.style.cssText = 'flex:1;padding:8px;border:1px solid #ccc;border-radius:4px 0 0 4px;font-size:13px;min-width:0;box-sizing:border-box;';
        this.tagInputBtn = document.createElement('button');
        this.tagInputBtn.textContent = 'OK';
        this.tagInputBtn.style.cssText = 'padding:8px 16px;border:1px solid #4CAF50;border-left:none;border-radius:0 4px 4px 0;background:#4CAF50;color:white;cursor:pointer;font-size:13px;';
        this.tagInputBtn.onclick = async () => {
            if (this.tagFilterEnabled) {
                this.currentPage = 1;
                await this.fetchAnimeData();
            }
        };
        tagInputRow.appendChild(this.tagInput);
        tagInputRow.appendChild(this.tagInputBtn);
        sidebar.appendChild(tagInputRow);

        this.selectTagBtn = document.createElement('button');
        this.selectTagBtn.textContent = '选择标签';
        this.selectTagBtn.style.cssText = 'padding:8px 16px;border:1px solid #ccc;border-radius:4px;background:#fff;color:#333;cursor:pointer;font-size:13px;margin-bottom:20px;';
        this.selectTagBtn.onclick = () => this.showTagMenu();
        sidebar.appendChild(this.selectTagBtn);

        filterCheckbox.onchange = () => {
            this.tagFilterEnabled = filterCheckbox.checked;
            this.tagInput.disabled = !this.tagFilterEnabled;
            this.tagInputBtn.disabled = !this.tagFilterEnabled;
            this.selectTagBtn.disabled = !this.tagFilterEnabled;
            if (!this.tagFilterEnabled) {
                this.tagInput.style.backgroundColor = '#eee';
                this.tagInput.style.color = '#999';
                this.tagInputBtn.style.backgroundColor = '#ccc';
                this.selectTagBtn.style.backgroundColor = '#eee';
                this.selectTagBtn.style.color = '#999';
                this.selectedTags = [];
                //this.tagInput.value = '';
                this.fetchAnimeData();
            } else {
                this.tagInput.style.backgroundColor = '#fff';
                this.tagInput.style.color = '#333';
                this.tagInputBtn.style.backgroundColor = '#4CAF50';
                this.selectTagBtn.style.backgroundColor = '#fff';
                this.selectTagBtn.style.color = '#333';
                if (this.tagInput.value.trim()) {
                    this.applyTagFilter();
                }
            }
        };

        this.tagInput.disabled = true;
        this.tagInputBtn.disabled = true;
        this.selectTagBtn.disabled = true;
        this.tagInput.style.backgroundColor = '#eee';
        this.tagInput.style.color = '#999';
        this.tagInputBtn.style.backgroundColor = '#ccc';
        this.selectTagBtn.style.backgroundColor = '#eee';
        this.selectTagBtn.style.color = '#999';

        const refreshBtn = document.createElement('button');
        refreshBtn.textContent = '刷新数据库';
        refreshBtn.style.cssText = 'padding:12px;border:none;border-radius:10px;background:#4A90D9;color:white;cursor:pointer;font-size:14px;margin-top:auto;';
        refreshBtn.onclick = () => this.refreshDatabase();
        sidebar.appendChild(refreshBtn);

        container.appendChild(sidebar);
        this.sidebar = sidebar;
    }

    applyTagFilter() {
        const tagNames = this.tagInput.value.split(',').map(s => s.trim()).filter(s => s);
        this.selectedTags = [];
        tagNames.forEach(name => {
            const tag = this.allTags.find(t => t.name === name);
            if (tag) {
                this.selectedTags.push(tag.id);
            }
        });
        this.fetchAnimeData();
    }

    showTagMenu() {
        const existingMenu = document.querySelector('.anime-tag-menu');
        if (existingMenu) {
            existingMenu.remove();
            const existingOverlay = document.querySelector('.anime-tag-overlay');
            if (existingOverlay) existingOverlay.remove();
            return;
        }

        const overlay = document.createElement('div');
        overlay.className = 'anime-tag-overlay';
        overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:999;';
        overlay.onclick = () => {
            menu.remove();
            overlay.remove();
        };
        document.body.appendChild(overlay);

        const menu = document.createElement('div');
        menu.className = 'anime-tag-menu';
        menu.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:500px;max-height:70vh;background:white;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:1000;display:flex;flex-direction:column;';

        const header = document.createElement('div');
        header.style.cssText = 'padding:15px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center;';
        header.innerHTML = '<span style="font-size:16px;font-weight:bold;">选择标签</span><div><button id="modeToggle" style="padding:6px 12px;border:1px solid #ccc;border-radius:4px;background:#fff;cursor:pointer;font-size:12px;margin-right:10px;">正选模式</button><button id="closeTagMenu" style="padding:6px 12px;border:none;border-radius:4px;background:#f0f0f0;cursor:pointer;font-size:12px;">关闭</button></div>';
        menu.appendChild(header);

        const modeToggle = header.querySelector('#modeToggle');
        const closeTagMenu = header.querySelector('#closeTagMenu');

        modeToggle.onclick = () => {
            this.selectionMode = this.selectionMode === 'positive' ? 'inverse' : 'positive';
            modeToggle.textContent = this.selectionMode === 'positive' ? '正选模式' : '反选模式';
        };

        closeTagMenu.onclick = () => {
            menu.remove();
            overlay.remove();
        };

        const tagListContainer = document.createElement('div');
        tagListContainer.style.cssText = 'flex:1;overflow-y:auto;padding:15px;';

        const groupedTags = {};
        this.allTags.forEach(tag => {
            const firstLetter = tag.pinyin ? tag.pinyin.charAt(0).toUpperCase() : '#';
            if (!groupedTags[firstLetter]) {
                groupedTags[firstLetter] = [];
            }
            groupedTags[firstLetter].push(tag);
        });

        Object.keys(groupedTags).sort().forEach(letter => {
            const letterDiv = document.createElement('div');
            letterDiv.style.cssText = 'margin-bottom:15px;';
            letterDiv.innerHTML = `<div style="font-size:14px;font-weight:bold;color:#333;margin-bottom:8px;">${letter}</div>`;

            const tagRow = document.createElement('div');
            tagRow.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;';

            groupedTags[letter].forEach(tag => {
                const tagItem = document.createElement('div');
                tagItem.style.cssText = 'display:flex;align-items:center;padding:4px 8px;background:#f5f5f5;border-radius:4px;';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.dataset.tagId = tag.id;
                checkbox.checked = this.selectedTags.includes(tag.id);
                checkbox.style.marginRight = '5px';

                const label = document.createElement('span');
                label.style.cssText = 'font-size:13px;';
                label.textContent = tag.name;

                tagItem.appendChild(checkbox);
                tagItem.appendChild(label);
                tagRow.appendChild(tagItem);
            });

            letterDiv.appendChild(tagRow);
            tagListContainer.appendChild(letterDiv);
        });

        menu.appendChild(tagListContainer);

        const footer = document.createElement('div');
        footer.style.cssText = 'padding:15px;border-top:1px solid #eee;display:flex;justify-content:flex-end;gap:10px;';
        footer.innerHTML = '<button id="confirmTagSelect" style="padding:8px 20px;border:none;border-radius:4px;background:#4CAF50;color:white;cursor:pointer;font-size:14px;">确定</button>';
        menu.appendChild(footer);

        footer.querySelector('#confirmTagSelect').onclick = () => {
            const checkboxes = tagListContainer.querySelectorAll('input[type="checkbox"]:checked');
            if (this.selectionMode === 'positive') {
                this.selectedTags = Array.from(checkboxes).map(cb => parseInt(cb.dataset.tagId));
            } else {
                const allTagIds = this.allTags.map(t => t.id);
                const checkedIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.tagId));
                this.selectedTags = allTagIds.filter(id => !checkedIds.includes(id));
            }
            this.tagInput.value = this.selectedTags.map(id => {
                const tag = this.allTags.find(t => t.id === id);
                return tag ? tag.name : '';
            }).join(',');
            menu.remove();
            const overlay = document.querySelector('.anime-tag-overlay');
            if (overlay) overlay.remove();
            this.currentPage = 1;
            this.fetchAnimeData();
        };

        document.body.appendChild(menu);
    }

    async createMainDisplay(container) {
        const mainDisplay = document.createElement('div');
        mainDisplay.style.cssText = 'flex:1;height:100%;padding:20px;display:flex;flex-direction:column;gap:20px;overflow:hidden;box-sizing:border-box;';

        const searchBar = document.createElement('div');
        searchBar.style.cssText = 'display:flex;gap:10px;padding-right:150px;';
        this.searchInput = document.createElement('input');
        this.searchInput.type = 'text';
        this.searchInput.placeholder = '搜索番剧...';
        this.searchInput.style.cssText = 'flex:1;padding:10px 15px;border:1px solid #ccc;border-radius:4px;font-size:14px;min-width:0;';
        const searchBtn = document.createElement('button');
        searchBtn.textContent = '搜索';
        searchBtn.style.cssText = 'padding:10px 20px;border:none;border-radius:4px;background:#4A90D9;color:white;cursor:pointer;font-size:14px;flex-shrink:0;';
        searchBtn.onclick = () => {};
        searchBar.appendChild(this.searchInput);
        searchBar.appendChild(searchBtn);
        mainDisplay.appendChild(searchBar);

        this.posterContainer = document.createElement('div');
        this.posterContainer.style.cssText = 'flex:1;display:grid;grid-template-columns:repeat(5,1fr);grid-template-rows:repeat(2,1fr);gap:20px;overflow:hidden;min-height:0;padding:5px;box-sizing:border-box;';
        mainDisplay.appendChild(this.posterContainer);

        this.paginationContainer = document.createElement('div');
        this.paginationContainer.style.cssText = 'display:flex;justify-content:center;align-items:center;gap:8px;padding:10px;';
        mainDisplay.appendChild(this.paginationContainer);

        container.appendChild(mainDisplay);
        this.mainDisplay = mainDisplay;
    }

    showLoading(message) {
        this.posterContainer.innerHTML = '';
        const loadingDiv = document.createElement('div');
        loadingDiv.style.cssText = 'grid-column:1/-1;display:flex;justify-content:center;align-items:center;font-size:16px;color:#666;';
        loadingDiv.textContent = message;
        this.posterContainer.appendChild(loadingDiv);
    }

    renderPosters(animeList) {
        this.posterContainer.innerHTML = '';
        animeList.forEach(anime => {
            const card = document.createElement('div');
            card.style.cssText = 'display:flex;flex-direction:column;background:rgba(255,255,255,0.05);border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);cursor:pointer;transition:transform 0.2s;min-height:0;';
            card.onmouseover = () => card.style.transform = 'translateY(-3px)';
            card.onmouseout = () => card.style.transform = 'translateY(0)';
            card.onclick = () => {
                const newPage = new_page();
                this.showAnimeDetail(anime.id, newPage);
            };

            const imgContainer = document.createElement('div');
            imgContainer.style.cssText = 'flex:1;min-height:0;padding:5px;width:calc(100% - 10px);background:rgba(255,255,255,0.1);overflow:hidden;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(3px);';
            
            const img = document.createElement('img');
            img.src = anime.poster || '';
            img.style.cssText = 'max-width:100%;max-height:100%;border-radius:8px;';
            img.onerror = () => { img.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%23ddd" width="100" height="100"/><text x="50" y="50" text-anchor="middle" dy=".3em" fill="%23999" font-size="12">无海报</text></svg>'; };
            
            imgContainer.appendChild(img);
            card.appendChild(imgContainer);

            const infoDiv = document.createElement('div');
            infoDiv.style.cssText = 'padding:5px;display:flex;flex-direction:column;gap:3px;align-items:center;background:rgba(255,255,255,0.9);';

            const titleDiv = document.createElement('div');
            titleDiv.style.cssText = 'font-size:14px;font-weight:bold;color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;width:100%;text-align:center;';
            titleDiv.textContent = anime.name;
            infoDiv.appendChild(titleDiv);

            const metaDiv = document.createElement('div');
            metaDiv.style.cssText = 'font-size:12px;color:#666;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;width:100%;text-align:center;';
            metaDiv.textContent = `${anime.year || ''} ${anime.tags ? anime.tags.join(', ') : ''}`;
            infoDiv.appendChild(metaDiv);

            card.appendChild(infoDiv);
            this.posterContainer.appendChild(card);
        });
    }

    renderPagination() {
        this.paginationContainer.innerHTML = '';
        const visiblePages = this.getVisiblePages();

        if (this.currentPage > 1) {
            const prevBtn = document.createElement('button');
            prevBtn.textContent = '上一页';
            prevBtn.style.cssText = 'padding:6px 12px;border:1px solid #ccc;border-radius:4px;background:#fff;cursor:pointer;';
            prevBtn.onclick = async () => {
                this.currentPage--;
                await this.fetchAnimeData();
            };
            this.paginationContainer.appendChild(prevBtn);
        }

        visiblePages.forEach(page => {
            if (page === '...') {
                const ellipsis = document.createElement('span');
                ellipsis.textContent = '...';
                ellipsis.style.cssText = 'padding:0 5px;color:#666;';
                this.paginationContainer.appendChild(ellipsis);
            } else {
                const btn = document.createElement('button');
                btn.textContent = page;
                btn.style.cssText = `padding:6px 12px;border:1px solid ${page === this.currentPage ? '#4A90D9' : '#ccc'};border-radius:4px;background:${page === this.currentPage ? '#4A90D9' : '#fff'};color:${page === this.currentPage ? '#fff' : '#333'};cursor:pointer;`;
                btn.onclick = async () => {
                    this.currentPage = page;
                    await this.fetchAnimeData();
                };
                this.paginationContainer.appendChild(btn);
            }
        });

        if (this.currentPage < this.totalPages) {
            const nextBtn = document.createElement('button');
            nextBtn.textContent = '下一页';
            nextBtn.style.cssText = 'padding:6px 12px;border:1px solid #ccc;border-radius:4px;background:#fff;cursor:pointer;';
            nextBtn.onclick = async () => {
                this.currentPage++;
                await this.fetchAnimeData();
            };
            this.paginationContainer.appendChild(nextBtn);
        }
    }

    getVisiblePages() {
        const pages = [];
        if (this.totalPages <= 7) {
            for (let i = 1; i <= this.totalPages; i++) pages.push(i);
        } else {
            if (this.currentPage <= 4) {
                for (let i = 1; i <= 5; i++) pages.push(i);
                pages.push('...');
                pages.push(this.totalPages);
            } else if (this.currentPage >= this.totalPages - 3) {
                pages.push(1);
                pages.push('...');
                for (let i = this.totalPages - 4; i <= this.totalPages; i++) pages.push(i);
            } else {
                pages.push(1);
                pages.push('...');
                for (let i = this.currentPage - 1; i <= this.currentPage + 1; i++) pages.push(i);
                pages.push('...');
                pages.push(this.totalPages);
            }
        }
        return pages;
    }

    async fetchAnimeData() {
        this.showLoading('加载中...');
        this.sendCommand('GET_ANIME_PAGE', {
            page: this.currentPage,
            pageSize: this.pageSize,
            sortBy: this.sortBy,
            sortOrder: this.sortOrder,
            tagFilterEnabled: this.tagFilterEnabled,
            selectedTags: this.selectedTags
        });
    }

    async refreshDatabase() {
        this.showLoading('数据库重建中...');
        this.sendCommand('REFRESH_ANIME_DATABASE');
    }

    showAnimeDetail(animeId, newPage) {
        const detailWidget = new CS_AnimeDetailWidget(animeId);
        detailWidget.render(newPage);
    }
}

class CS_AnimeDetailWidget {
    constructor(animeId) {
        this.animeId = animeId;
        this.detail = null;
    }

    render(container) {
        container.innerHTML = '';
        container.style.position = 'relative';
        container.style.height = '100%';
        container.style.overflow = 'hidden';

        const messageHandler = (data) => {
            if (data.command === 'ANIME_DETAIL_DATA' && data.widgetId === 'anime_detail_' + this.animeId) {
                this.handleCommand(data.command, data);
            }
        };

        if (typeof message_proc_func_list !== 'undefined') {
            message_proc_func_list.push(messageHandler);
        }

        if (container.cleanFuncList) {
            container.cleanFuncList.push(() => {
                const idx = message_proc_func_list ? message_proc_func_list.indexOf(messageHandler) : -1;
                if (idx !== -1) message_proc_func_list.splice(idx, 1);
            });
        }

        cs_createBackButtons(container);

        const contentDiv = document.createElement('div');
        contentDiv.style.cssText = 'position:absolute;top:10px;bottom:10px;left:50%;transform:translateX(-50%);width:70%;background:rgba(255,255,255,0.6);border-radius:10px;overflow-y:auto;display:flex;gap:30px;padding:20px;';
        container.appendChild(contentDiv);

        const posterDiv = document.createElement('div');
        posterDiv.style.cssText = 'flex:0 0 300px;display:flex;align-items:flex-start;justify-content:center;';
        contentDiv.appendChild(posterDiv);

        const posterImg = document.createElement('img');
        posterImg.style.cssText = 'width:100%;max-height:500px;object-fit:contain;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.2);';
        posterDiv.appendChild(posterImg);

        const infoDiv = document.createElement('div');
        infoDiv.style.cssText = 'flex:1;display:flex;flex-direction:column;gap:15px;min-width:0;';
        contentDiv.appendChild(infoDiv);

        const nameDiv = document.createElement('div');
        nameDiv.style.cssText = 'font-size:24px;font-weight:bold;color:#333;';
        infoDiv.appendChild(nameDiv);

        const timeDiv = document.createElement('div');
        timeDiv.style.cssText = 'font-size:14px;color:#666;';
        infoDiv.appendChild(timeDiv);

        const tagsDiv = document.createElement('div');
        tagsDiv.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;';
        infoDiv.appendChild(tagsDiv);

        const introTitleDiv = document.createElement('div');
        introTitleDiv.style.cssText = 'font-size:16px;font-weight:bold;color:#333;margin-top:10px;';
        introTitleDiv.textContent = '简介';
        infoDiv.appendChild(introTitleDiv);

        const introContentDiv = document.createElement('div');
        introContentDiv.style.cssText = 'font-size:14px;color:#555;line-height:1.6;';
        infoDiv.appendChild(introContentDiv);

        const introSrcDiv = document.createElement('div');
        introSrcDiv.style.cssText = 'font-size:12px;color:#888;margin-top:5px;';
        infoDiv.appendChild(introSrcDiv);

        const danmuRowDiv = document.createElement('div');
        danmuRowDiv.style.cssText = 'display:flex;align-items:center;gap:5px;margin-top:10px;flex-wrap:wrap;';
        infoDiv.appendChild(danmuRowDiv);

        const danmuTitleDiv = document.createElement('div');
        danmuTitleDiv.style.cssText = 'font-size:16px;font-weight:bold;color:#333;';
        danmuTitleDiv.textContent = '弹幕';
        danmuRowDiv.appendChild(danmuTitleDiv);

        const danmuStatusDiv = document.createElement('div');
        danmuStatusDiv.style.cssText = 'font-size:14px;color:#555;';
        danmuRowDiv.appendChild(danmuStatusDiv);

        const danmuSourcesLabelDiv = document.createElement('div');
        danmuSourcesLabelDiv.style.cssText = 'font-size:14px;color:#555;white-space:pre;';
        danmuSourcesLabelDiv.textContent = '  弹幕来源:';
        danmuRowDiv.appendChild(danmuSourcesLabelDiv);

        const danmuSourcesDiv = document.createElement('div');
        danmuSourcesDiv.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;';
        danmuRowDiv.appendChild(danmuSourcesDiv);

        const episodeTitleDiv = document.createElement('div');
        episodeTitleDiv.style.cssText = 'font-size:16px;font-weight:bold;color:#333;margin-top:10px;';
        episodeTitleDiv.textContent = '剧集';
        infoDiv.appendChild(episodeTitleDiv);

        const episodeListDiv = document.createElement('div');
        episodeListDiv.style.cssText = 'display:flex;flex-wrap:wrap;gap:10px;';
        infoDiv.appendChild(episodeListDiv);

        this.posterImg = posterImg;
        this.nameDiv = nameDiv;
        this.timeDiv = timeDiv;
        this.tagsDiv = tagsDiv;
        this.introContentDiv = introContentDiv;
        this.introSrcDiv = introSrcDiv;
        this.danmuStatusDiv = danmuStatusDiv;
        this.danmuSourcesDiv = danmuSourcesDiv;
        this.danmuSourcesLabelDiv = danmuSourcesLabelDiv;
        this.episodeListDiv = episodeListDiv;
        this.contentDiv = contentDiv;

        this.fetchDetail();
    }

    async fetchDetail() {
        this.sendCommand('GET_ANIME_DETAIL', { animeId: this.animeId });
    }

    handleCommand(command, data) {
        if (command === 'ANIME_DETAIL_DATA') {
            this.detail = data.animeDetail;
            this.renderDetail();
        }
    }

    sendCommand(command, data = {}) {
        if (socket && socket.isConnected()) {
            socket.send(JSON.stringify({
                command: command,
                widgetId: 'anime_detail_' + this.animeId,
                ...data
            }));
        }
    }

    renderDetail() {
        const d = this.detail;
        if (!d) return;

        this.posterImg.src = d.coverPath || '';
        this.posterImg.onerror = () => { this.posterImg.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%23ddd" width="100" height="100"/><text x="50" y="50" text-anchor="middle" dy=".3em" fill="%23999" font-size="12">无海报</text></svg>'; };

        this.nameDiv.textContent = d.mdName || d.name || '未知名称';

        const year = d.mdYear || d.year;
        const month = d.mdMonth || d.month;
        if (year) {
            this.timeDiv.textContent = month ? `${year}年${month}月` : `${year}年`;
        } else {
            this.timeDiv.textContent = '时间未知';
        }

        this.tagsDiv.innerHTML = '';
        const allTags = [...(d.tags || []), ...(d.dbTags || [])];
        const uniqueTags = [...new Set(allTags)];
        uniqueTags.forEach(tag => {
            const tagSpan = document.createElement('span');
            tagSpan.style.cssText = 'padding:4px 10px;background:#e3f2fd;color:#1976d2;border-radius:12px;font-size:12px;';
            tagSpan.textContent = tag;
            this.tagsDiv.appendChild(tagSpan);
        });

        const addTagSpan = document.createElement('span');
        addTagSpan.style.cssText = 'padding:4px 10px;background:#1976d2;color:white;border-radius:12px;font-size:12px;cursor:pointer;transition:background 0.2s;display:inline-flex;align-items:center;gap:2px;';
        addTagSpan.innerHTML = '<svg width="16" height="16" viewBox="0 0 100 100"><path d="M50,10 V90 M10,50 H90" stroke="white" stroke-width="10" fill="none"/></svg> 编辑标签';
        addTagSpan.onmouseenter = () => { addTagSpan.style.background = '#42a5f5'; };
        addTagSpan.onmouseleave = () => { addTagSpan.style.background = '#1976d2'; };
        addTagSpan.onclick = () => {
            //this.showTagMenu();
        };
        this.tagsDiv.appendChild(addTagSpan);

        if (d.introduction) {
            this.introContentDiv.textContent = d.introduction;
        } else {
            this.introContentDiv.textContent = '暂无简介';
            this.introContentDiv.style.color = '#999';
        }

        if (d.introductionSrc) {
            const srcName = d.introductionSrc['src-name'] || '';
            const srcUrl = d.introductionSrc['src-url'] || '';
            if (srcName) {
                if (srcUrl) {
                    this.introSrcDiv.innerHTML = `来源: <a href="${srcUrl}" target="_blank" style="color:#4A90D9;">${srcName}</a>`;
                } else {
                    this.introSrcDiv.textContent = `来源: ${srcName}`;
                }
            }
        }

        this.danmuStatusDiv.textContent = d.hasDanmu ? '有弹幕' : '无弹幕';
        this.danmuStatusDiv.style.color = d.hasDanmu ? '#FF69B4' : '#999';

        this.danmuSourcesDiv.innerHTML = '';
        if (d.danmuSources && d.danmuSources.length > 0) {
            this.danmuSourcesLabelDiv.style.display = '';
            d.danmuSources.forEach(src => {
                const srcSpan = document.createElement('span');
                srcSpan.style.cssText = 'padding:4px 10px;background:#1976d2;color:#fff;border-radius:12px;font-size:12px;border:1px solid #1565c0;';
                srcSpan.textContent = src;
                this.danmuSourcesDiv.appendChild(srcSpan);
            });
        } else {
            this.danmuSourcesLabelDiv.style.display = 'none';
        }

        this.episodeListDiv.innerHTML = '';
        if (d.episodes && d.episodes.length > 0) {
            d.episodes.forEach(ep => {
                const epBtn = document.createElement('button');
                epBtn.style.cssText = 'position:relative;width:120px;padding:12px 16px;border:1px solid #ccc;border-radius:8px;background:#fff;color:#333;cursor:pointer;font-size:13px;text-align:left;transition:all 0.3s;';
                epBtn.onmouseover = () => { epBtn.style.background = 'rgba(227,242,253,1.0)'; epBtn.style.color = '#fff'; };
                epBtn.onmouseout = () => { epBtn.style.background = '#fff'; epBtn.style.color = '#333'; epBtn.style.borderColor = '#ccc'; };

                const orderDiv = document.createElement('div');
                orderDiv.style.cssText = 'font-size:15px;font-weight:bold;color:#333;';
                orderDiv.textContent = `第${ep.order}集`;
                epBtn.appendChild(orderDiv);

                if (ep.name) {
                    const nameDiv = document.createElement('div');
                    nameDiv.style.cssText = 'font-size:12px;color:#888;margin-top:3px;';
                    nameDiv.textContent = ep.name;
                    epBtn.appendChild(nameDiv);
                } else {
                    orderDiv.style.cssText = 'font-size:15px;font-weight:bold;color:#333;text-align:center;';
                    epBtn.style.justifyContent = 'center';
                    epBtn.style.alignItems = 'center';
                    epBtn.style.display = 'flex';
                }

                if (ep.hasDanmu) {
                    const danmuBadge = document.createElement('div');
                    danmuBadge.style.cssText = 'position:absolute;top:4px;right:4px;padding:2px 6px;background:#FF69B4;color:#fff;border-radius:10px;font-size:10px;';
                    danmuBadge.textContent = '有弹幕';
                    epBtn.appendChild(danmuBadge);
                }

                // 添加点击事件，打开播放器页面
                epBtn.onclick = () => {
                    const newPage = new_page();
                    const playerWidget = new CS_AnimeVideoPlayerWidget(d.rootPath, d.episodes, ep);
                    playerWidget.render(newPage);
                };

                this.episodeListDiv.appendChild(epBtn);
            });
        } else {
            const noEp = document.createElement('div');
            noEp.style.cssText = 'font-size:13px;color:#999;';
            noEp.textContent = '暂无剧集信息';
            this.episodeListDiv.appendChild(noEp);
        }
    }
}

/**
 * 通用视频播放器页面组件。
 */
const CS_COMMENT_TOTAL_CARTOON_FONT_DATA_URL =
    'data:font/woff2;base64,d09GMgABAAAAAASYAA4AAAAACBwAAARHAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHBoGVgAsColAhlMBNgIkAywLGAAEIAWBLAcgDAgXJBgYG6QFUZTMTQ3kZ0K8dRjraR1SKijeYeA7QQR61GxwAPWAcg+rlotaNUsA6Vzj8HdDetXMbk7Jrmd8UJLzA+roooW6E5J/Byc/wOq+EnpWVKJU3A7cVDtf4DzyxBM7l+ICCuw8DTiL8J5tOJ/IhAZO022YrSjg7/woqvSD/ygC2OCBFzJ1ePY0rAAAEAzZjY4dBgbgtCYNbCmysVTRrVly4adTpk8fpYgksvliijdfyLEKBFUK7dAIAqiBEsk2TSDJBP0IgbLF9fBIgywH2QVxaEATBenfqyAuLi/nulman1lUEi5eg6mNXWA4ploenqgpPVlMHNYKjFx8VHbAGg/odXr41NeO+lWjauYAG5n07YHwoI3ltkb65lE8BAzOZAc5CF82uaOq5z0sWBPpm1elb6iDnT5HzaO8jZl44IA9gGLHCsVVepJ49WlfnjS8Qgs5a8KPlTmoVXc1zbND6qSGJG36uuXGVN/Tp8QyhmFNYA+X9qSbxvD4wZ25UrfQoR/VQYVbGb6qDwGjDa7xft522N2lPqyxifUW6TCHeO/4K/mvOn2uFg9lYp1ZxFI9t3PTSYwX70piIUd1bIRNj2LaQYYhnaPBOyvP9GCeODnpKGste4mu47xaHfE5VOpTWFInltkcdnN1X0x5a7xGgg5gd2NJXM16WasxTL7ynwvbmi2+9MitGI8MLNpWuaIiKGY3Ijllikye3qvI1Mkdk18fvBnLmDihGtw8pgS1SBDaefvYhz/W4h6KqtGBUhKKBm1QbRRdW4L/cNr5pN65G7wT4H8ZQU5AedEZ+dXJs/eps722Y3G1w1z705a9eM/eNeNRsFHTG9jTFQJB8GC2eHzxcUTE//L3KeO7UiZ9mRZ2+IMAadvLioIBjwfJZ5LpIM1qqeqTkqFZYp+UmpueHhQUQPdUQKC62jXy/iU1MXnK6MWrk3NDQHF3kDk5sXr8kXq2FbjKcssq9+zIQ8Yun1/glbYk9M+371unWQ4dxjllTPO+d0GWG74WRSirsJpa8+zhzEU4pwVyIZws2tz0V1IXjI9fjSvnipQh3UOpLrnsNO/lMVa8DlZgaiJ+b7+enrT875Obu8WkXw8qJXRNpWs4fmF6hBbGYXz1gpCFJcGDtlWTQxbZd8cvBExMltnu0asvvQ7rsEvHbSPXzy33Wnh/p3KkeZ4qooqMemTeWGvf+dM6/WCSX8/s3OKY99PKGmlVuHHbwgfgbsxvJqLwBXBD8VOTuYxg/jETi2ElKigxFmPJfLw4TmEh9o76dHQJtAM1kMAB8anLwOn34VjdMGeW9KAimjUQAZAEGyIkBQeSqqqmqpGkY0VB3AI7KqhiIbi55JAIL+ESmMJ0Z/R4ZpQ5zNr1o3FohdE6vNuHFsb18UXMZJj5pNk4SdipYQbDLGQOs1FpSuZj7Ni/JeaGW8gOBDBMA9aYlIBCibT300A3FdTRSeTlh9EK';

const CS_COMMENT_DIV_TEMPLATE =
`<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>B站评论展示</title>
    <style>
        .cs-cmt-v1-root * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        .cs-cmt-v1-root {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f5f5f5;
            display: flex;
            flex-direction: column;
            width: 100%;
            min-height: 100%;
            flex: 1 0 auto;
        }
        .cs-cmt-v1-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .cs-cmt-v1-header {
            background: linear-gradient(135deg, #fb7299 0%, #ff7cce 100%);
            color: white;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(251, 114, 153, 0.3);
        }
        .cs-cmt-v1-header h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .cs-cmt-v1-header p {
            opacity: 0.9;
            font-size: 14px;
        }
        .cs-cmt-v1-comment-list {
            background: white;
            padding: 16px;
            width: 100%;
            min-height: 100%;
            flex: 1 0 auto;
            box-sizing: border-box;
        }
        .cs-cmt-v1-comment-list.cs-cmt-v1-comment-list-empty {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #9499a0;
            font-size: 15px;
            text-align: center;
        }
        .cs-cmt-v1-comment-item {
            padding: 16px 0;
            border-bottom: 1px solid #f0f0f0;
            position: relative;
        }
        .cs-cmt-v1-comment-item:last-child {
            border-bottom: none;
        }
        .cs-cmt-v1-comment-header {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        .cs-cmt-v1-avatar {
            width: 48px;
            height: 48px;
            margin-right: 12px;
            flex-shrink: 0;
            border: 2px solid transparent;
            position: relative;
            overflow: visible;
        }
        .cs-cmt-v1-avatar-canvas {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        .cs-cmt-v1-avatar-layer {
            position: absolute;
        }
        .cs-cmt-v1-avatar-layer img {
            display: block;
        }
        .cs-cmt-v1-user-info {
            flex: 1;
            min-width: 0;
        }
        .cs-cmt-v1-username {
            font-weight: 600;
            font-size: 15px;
            color: #18191c;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .cs-cmt-v1-level-badge {
            width: 30px;
            height: 30px;
        }
        .cs-cmt-v1-vip-username {
            color: #fb7299;
        }
        .cs-cmt-v1-reply-username.cs-cmt-v1-vip-username {
            color: #fb7299;
        }
        .cs-cmt-v1-vip-avatar-badge {
            position: absolute;
            bottom: 0;
            right: 0;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            border: 2px solid white;
            box-sizing: content-box;
            z-index: 2;
        }
        .cs-cmt-v1-meta-info {
            font-size: 12px;
            color: #9499a0;
            display: flex;
            gap: 12px;
        }
        .cs-cmt-v1-comment-content {
            margin-left: 60px;
            margin-bottom: 12px;
            line-height: 24px;
            font-size: 15px;
            color: #18191c;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .cs-cmt-v1-comment-content img {
            vertical-align: text-bottom;
            max-height: 24px;
            margin: 0 2px;
        }
        .cs-cmt-v1-comment-picture {
            margin-left: 60px;
            margin-top: 8px;
            margin-bottom: 6px;
        }
        .cs-cmt-v1-comment-picture.cs-cmt-v1-single img {
            max-width: 210px;
            max-height: 180px;
            border-radius: 6px;
            cursor: zoom-in;
        }
        .cs-cmt-v1-comment-picture.cs-cmt-v1-grid {
            display: grid;
            grid-template-columns: repeat(4, 92px);
            gap: 4px;
        }
        .cs-cmt-v1-comment-picture.cs-cmt-v1-grid .cs-cmt-v1-picture-item {
            width: 88px;
            height: 88px;
            border-radius: 6px;
            overflow: hidden;
            cursor: zoom-in;
            position: relative;
        }
        .cs-cmt-v1-comment-picture.cs-cmt-v1-grid .cs-cmt-v1-picture-item img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .cs-cmt-v1-comment-item {
            position: relative;
        }
        .cs-cmt-v1-cardBg {
            position: absolute;
            top: 0;
            right: 0;
            height: 48px;
            cursor: pointer;
            display: flex;
            align-items: center;
        }
        .cs-cmt-v1-cardBg img {
            height: 100%;
            border-radius: 4px;
        }
        .cs-cmt-v1-cardBg .cs-cmt-v1-card-text {
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            font-family: 'fans-num';
            font-size: 10px;
            line-height: 12px;
            text-align: left;
            display: flex;
            flex-direction: column;
            padding-right: 4px;
        }
        .cs-cmt-v1-cardBg .cs-cmt-v1-card-text span {
            display: block;
        }
        .cs-cmt-v1-cardBg .cs-cmt-v1-tooltip {
            display: none;
            position: absolute;
            top: 100%;
            right: 14px;
            border: 1px solid gainsboro;
            background: white;
            color: black;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            white-space: nowrap;
            z-index: 100;
            margin-bottom: 8px;
            box-shadow: rgba(0, 0, 0, 0.1) 0px 0px 30px 2px;
        }
        .cs-cmt-v1-cardBg:hover .cs-cmt-v1-tooltip {
            display: block;
        }
        .cs-cmt-v1-cardBg .cs-cmt-v1-tooltip .cs-cmt-v1-tooltip-name {
            font-weight: bold;
            margin-bottom: 4px;
        }
        .cs-cmt-v1-cardBg .cs-cmt-v1-tooltip .cs-cmt-v1-tooltip-id {
            color: #9499a0;
        }
        .cs-cmt-v1-comment-footer {
            margin-left: 60px;
            display: flex;
            align-items: center;
            gap: 24px;
        }
        .cs-cmt-v1-action-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            color: #9499a0;
            cursor: pointer;
            transition: all 0.2s;
        }
        .cs-cmt-v1-action-btn:hover {
            color: #00A1D6;
        }
        .cs-cmt-v1-action-btn:hover img {
            filter: invert(39%) sepia(90%) saturate(2000%) hue-rotate(170deg) brightness(95%) contrast(100%);
        }
        .cs-cmt-v1-action-btn span {
            font-weight: 500;
        }
        .cs-cmt-v1-jump-link {
            color: #008AC5;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 1px;
            vertical-align: bottom;
        }
        .cs-cmt-v1-jump-link:hover {
            color: #00aeec;
        }
        .cs-cmt-v1-timestamp {
            color: #9499a0;
            font-size: 13px;
            font-family: "HarmonyOS_Regular",Helvetica Neue, Microsoft YaHei, sans-serif !important;
        }
        .cs-cmt-v1-reply-section {
            margin-top: 12px;
            margin-left: 60px;
            padding-left: 16px;
            border-left: 2px solid #e9e9eb;
        }
        .cs-cmt-v1-reply-item {
            padding: 12px 0;
            border-bottom: 1px solid #f5f5f5;
        }
        .cs-cmt-v1-reply-item:last-child {
            border-bottom: none;
        }
        .cs-cmt-v1-reply-header {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        .cs-cmt-v1-reply-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            overflow: visible;
            margin-right: 10px;
            flex-shrink: 0;
            position: relative;
        }
        .cs-cmt-v1-reply-avatar .cs-cmt-v1-avatar-canvas {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        .cs-cmt-v1-reply-avatar .cs-cmt-v1-avatar-layer {
            position: absolute;
        }
        .cs-cmt-v1-reply-avatar .cs-cmt-v1-avatar-layer img {
            display: block;
        }
        .cs-cmt-v1-reply-username {
            font-weight: 500;
            font-size: 14px;
            color: #18191c;
            margin-bottom: 2px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .cs-cmt-v1-reply-meta {
            font-size: 11px;
            color: #9499a0;
        }
        .cs-cmt-v1-reply-content {
            margin-left: 46px;
            line-height: 1.6;
            font-size: 14px;
            color: #18191c;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .cs-cmt-v1-reply-content img {
            vertical-align: text-bottom;
            max-height: 20px;
            margin: 0 2px;
        }
        .cs-cmt-v1-reply-footer {
            margin-left: 46px;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 24px;
        }
        .cs-cmt-v1-expand-btn {
            margin-left: 60px;
            margin-top: 8px;
            color: #00a1d6;
            font-size: 13px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .cs-cmt-v1-expand-btn:hover {
            text-decoration: underline;
        }
        .cs-cmt-v1-reply-expand-btn {
            margin-top: 8px;
            color: #9499a0;
            font-size: 13px;
            cursor: pointer;
        }
        .cs-cmt-v1-reply-expand-btn:hover {
            color: #00a1d6;
        }
        .cs-cmt-v1-reply-pagination {
            margin-left: 60px;
            margin-top: 12px;
            margin-bottom: 8px;
            font-size: 13px;
            color: #000000;
            display: flex;
            align-items: center;
            gap: 4px;
            flex-wrap: wrap;
            bottom: 0;
            background: white;
            z-index: 10;
        }
        .cs-cmt-v1-reply-pagination .cs-cmt-v1-page-count {
            margin-right: 10px;
        }
        .cs-cmt-v1-reply-pagination .cs-cmt-v1-page-num {
            color: #000000;
            cursor: pointer;
            padding: 2px 1px;
        }
        .cs-cmt-v1-reply-pagination .cs-cmt-v1-page-num:hover {
            color: #00AEEC;
        }
        .cs-cmt-v1-reply-pagination .cs-cmt-v1-page-num.cs-cmt-v1-active {
            color: #00AEEC;
        }
        .cs-cmt-v1-reply-pagination .cs-cmt-v1-page-ellipsis {
            color: #000000;
        }
        .cs-cmt-v1-reply-pagination .cs-cmt-v1-page-btn {
            color: #000000;
            cursor: pointer;
        }
        .cs-cmt-v1-reply-pagination .cs-cmt-v1-page-btn:hover {
            color: #00AEEC;
        }
        .cs-cmt-v1-count-badge {
            display: inline-block;
            background: #f4f4f4;
            color: #9499a0;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
        }
    </style>
</head>
<body>
        <div class="cs-cmt-v1-comment-list">
            
        </div>
</body>
</html>`
//[DEBUG-START] 性能调试代码，release时删掉
// 临时评论性能诊断开关，与后端 COMMENT_PERF_DEBUG 分别控制。
const CS_COMMENT_PERF_DEBUG = true;
//[DEBUG-END]
class CS_VideoPlayerWidget {
    constructor(rootPath, episodes, currentEpisode, haveEpisodeBar = false, haveComment = false) {
        /**
        初始化视频播放器组件
        :param rootPath: 视频根路径

        :param episodes: [
            {
                'order': Number,
                'name': String,
                'path': String,
                'hasDanmu': Boolean,
                'danmuSources': Array
            },...
        ] 
        剧集列表。

        :param currentEpisode: {
                'order': Number,
                'name': String,
                'path': String,
                'hasDanmu': Boolean,
                'danmuSources': Array
            }
        当前剧集。

        :param haveEpisodeBar: 是否在播放器下方创建剧集列表栏。

        :param haveComment: 是否启用评论展示面板。
        */
        this.rootPath = rootPath; // 当前视频文件所在的根目录。
        this.episodes = episodes || []; // 当前视频的全部剧集信息列表。
        this.currentEpisode = currentEpisode; // 当前选中并准备播放的剧集信息。
        this.haveEpisodeBar = Boolean(haveEpisodeBar); // 是否创建并显示剧集列表栏。
        this.haveComment = Boolean(haveComment); // 是否创建评论展示按钮和面板。
        this.episodeScrollContainer = null; // 剧集列表的横向滚动容器，未启用剧集栏时为空。
        this.playerContainer = null; // 播放器容器元素。
        this.playerLayout = null; // 同时容纳播放器和评论面板的弹性布局容器。
        this.commentPanel = null; // 可在球形按钮与评论矩形面板之间切换的元素。
        this.commentIcon = null; // 评论球形按钮中显示的 SVG 图标。
        this.commentCollapseButton = null; // 评论面板右上角的“收起”按钮。
        this.commentBackButtonBar = null; // 评论按钮收起时所属的返回按钮栏。
        this.commentExpanded = false; // 评论面板当前是否处于展开状态。
        this.commentAnimation = null; // 评论面板当前正在执行的形变动画。
        this.playerCommentAnimation = null; // 评论展开或收起时播放器的位置与尺寸动画。
        this.commentExpandedLayoutHeight = 0; // 评论展开期间锁定的播放器布局高度。
        this.commentContent = null; // 评论面板展开后显示的全部界面内容。
        this.commentScrollContainer = null; // 评论内容的普通纵向滚动 div。
        this.commentRoot = null; // 使用 cs-cmt-v1- 命名空间隔离样式和节点的评论根 div。
        this.commentList = null; // 普通评论根 div 中承载后端评论 HTML 的列表元素。
        this.commentScrollbarCleanup = null; // 普通评论滚动 div 的美化滚动条清理函数。
        this.commentFontStyleElement = null; // 注册到父文档的评论字体声明。
        this.commentImagePreviewModal = null; // 位于当前 .page 中、由组件实例控制的评论图片预览层。
        this.commentTotalNumber = null; // 顶部“共 x 条评论”的数字元素。
        this.commentSourceCount = null; // 当前来源评论数量元素。
        this.commentSourceButton = null; // 当前评论来源选择按钮。
        this.commentSourceMenu = null; // 评论来源下拉菜单。
        this.commentSourceInfoPopover = null; // 评论来源详情悬浮窗口。
        this.commentOptionsPopover = null; // 排序、搜索和筛选选项窗口。
        this.commentSettingsPopover = null; // 选项窗口中的高级筛选下拉窗口。
        this.commentPagination = null; // 评论页码按钮容器。
        this.commentPageSizeInput = null; // 每页评论数量的可输入下拉框。
        this.commentPageSizeMenu = null; // 与每页数量输入框等宽的预设值菜单。
        this.commentWordCountMenu = null; // 与字数输入框等宽的预设值菜单。
        this.commentOutsideClickHandler = null; // 点击面板外部时关闭悬浮窗口的处理函数。
        this.commentKeywordTimer = null; // 关键词输入防抖计时器。
        this.commentTemplate = CS_COMMENT_DIV_TEMPLATE; // 用于构建普通评论 div 的样式模板。
        this.commentPreviewImages = []; // 当前图片预览组的资源地址。
        this.commentPreviewIndex = 0; // 当前预览图片在图片组中的索引。
        this.commentPreviewZoomed = false; // 当前预览图片是否处于原尺寸缩放状态。
        this.commentPreviewDragging = false; // 当前是否正在拖动放大后的预览图片。
        this.commentPreviewDragMoved = false; // 单次按下后是否实际发生拖动。
        this.commentPreviewStartX = 0; // 预览图拖动开始位置的横坐标。
        this.commentPreviewStartY = 0; // 预览图拖动开始位置的纵坐标。
        this.commentPreviewTranslateX = 0; // 预览图当前横向位移。
        this.commentPreviewTranslateY = 0; // 预览图当前纵向位移。
        this.commentInfo = null; // 后端返回的当前视频评论概要信息。
        this.commentSources = []; // 当前视频可选择的评论来源列表。
        this.commentCurrentSource = null; // 当前正在展示的评论来源。
        this.commentCurrentPage = 1; // 当前评论页码。
        this.commentTotalPages = 1; // 当前筛选条件下的评论总页数。
        this.commentFilteredCount = 0; // 当前筛选条件命中的顶层评论数量。
        this.commentInfoRequestId = ''; // 当前有效的评论信息请求编号。
        this.commentHtmlRequestId = ''; // 当前有效的评论 HTML 请求编号。
        //[DEBUG-START] 性能调试代码，release时删掉
        this.commentPerformanceRequest = null; // 仅保存最新请求的性能计时，避免累积。
        //[DEBUG-END]
        this.commentSourceInfoRequestId = ''; // 当前有效的评论来源信息修改请求编号。
        this.commentSourceInfoPending = null; // 来源名称保存失败时用于回滚的待确认修改。
        this.commentRequestSerial = 0; // 生成评论请求编号的递增序号。
        this.commentSettings = { // 评论面板的可持久化显示设置。
            pageSize: 20,
            sortBy: 'time',
            markDeleted: false,
            onlyDeleted: false,
            onlyVip: false,
            wordFilterEnabled: false,
            wordCount: 0,
            wordDirection: 'above'
        };
        this.player = null; // NPlayer 播放器实例。
        this.danmakuData = null; // 当前剧集加载到的弹幕数据。
        this.widgetId = `cs_video_player_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`; // 当前播放器组件的唯一消息路由标识。
        this.messageHandler = null; // 处理后端 WebSocket 文本消息的函数。

        this.binaryMessageHandler = null; // 处理后端视频流二进制消息的函数。
        this.mediaSource = null; // 向 video 元素提供媒体流的 MediaSource 实例。
        this.sourceBuffer = null; // 向 MediaSource 追加 fMP4 分段的 SourceBuffer。
        this.streamObjectUrl = null; // 由 MediaSource 创建并设置给 video.src 的 Blob URL。
        this.activeStreamId = null; // 当前后端视频流会话的唯一标识。
        this.streamQueue = []; // 等待依次写入 SourceBuffer 的视频分段队列。
        this.currentStreamSegment = null; // 当前正在写入 SourceBuffer 的视频分段。
        this.streamEnded = false; // 后端是否已经发送当前视频流的结束消息。
        this.streamStartTime = 0; // 当前视频流在整部视频时间轴上的起始秒数。
        this.streamDuration = 0; // 当前视频文件的总时长（秒）。
        this.streamSeekTimer = null; // 对进度条拖动请求进行防抖的定时器。
        this.streamSeekingHandler = null; // video 元素 seeking 事件的处理函数。
        this.streamPlayHandler = null; // video 元素 play 事件的处理函数。
        this.streamTimeUpdateHandler = null; // video 元素 timeupdate 事件的处理函数。
        this.streamWaitingHandler = null; // video 元素 waiting 事件的处理函数。
        this.streamPrebufferSeconds = 12; // 新流开始播放前要求预先缓冲的秒数。
        this.streamBufferLowWaterSeconds = 10; // 触发请求后续数据的前向缓冲低水位。
        this.streamBufferHighWaterSeconds = 30; // 每次请求希望补充到的前向缓冲高水位。
        this.streamRetainBehindSeconds = 60; // 播放位置后方需要保留的历史缓冲秒数。
        this.streamRequestedUntil = 0; // 当前已向后端请求到的视频时间点。
        this.streamLastTrimBefore = 0; // 上一次清理历史缓冲时使用的截止时间点。
        this.streamPrebufferNoticeShown = false; // 是否已经显示本轮预缓冲提示。
        this.restartingStream = false; // 当前是否正在首次建立或 Seek 后重建视频流。
        this.resumeAfterStreamOpen = false; // 新流缓冲完成后是否需要自动恢复播放。
        this.streamFailed = false; // 当前重封装视频流是否已经进入失败状态。
        this.streamUnsupportedNotice = null; // 不支持视频编码时显示的提示层元素。
    }

    render(container) {
        container.innerHTML = '';
        container.style.position = 'relative';
        container.style.height = '100%';
        container.style.overflow = 'hidden';
        container.style.background = 'linear-gradient(135deg, #1e1e2f, #2a2a40)';

        // 添加消息处理函数
        this.messageHandler = (data) => {
            if (data.command === 'CS_VIDEO_DATA' && data.widgetId === this.widgetId) {
                const hasDanmaku = data['has-danmaku'];
                if (hasDanmaku) {
                    this.danmakuData = data['danmaku-data'] || null;
                    console.log('收到弹幕数据:', this.danmakuData);
                } else {
                    this.danmakuData = null;
                    console.log('该视频没有弹幕');
                }
                // 保存自动跳转时间
                this.autoSeekTime = data['auto-seek-time'] || 0;
                console.log('自动跳转时间:', this.autoSeekTime);
                this.initPlayer(this.playerContainerId);
            } else if (data.command === 'DANMAKU_CONFIG_SAVED' && data.widgetId === this.widgetId) {
                console.log('弹幕配置保存成功');
            } else if (data.command === 'WATCH_RECORD_SAVED' && data.widgetId === this.widgetId) {
                console.log('观看记录保存成功:', data.success);
            } else if (data.command === 'CS_COMMENT_INFO' && data.widgetId === this.widgetId) {
                this.handleCommentInfo(data);
            } else if (data.command === 'CS_COMMENT_HTML' && data.widgetId === this.widgetId) {
                this.handleCommentHtml(data);
            } else if (data.command === 'CS_COMMENT_SETPAGE' && data.widgetId === this.widgetId) {
                if (data.requestId === this.commentHtmlRequestId) {
                    this.commentCurrentPage = Math.max(1, Number(data.page) || 1);
                    this.commentTotalPages = Math.max(1, Number(data.totalPages) || 1);
                    this.renderCommentPagination();
                }
            } else if (data.command === 'CS_COMMENT_SOURCEINFO_SET'
                && data.widgetId === this.widgetId) {
                this.handleCommentSourceInfoSet(data);
            } else if (data.command === 'CS_COMMENT_ERROR' && data.widgetId === this.widgetId) {
                this.handleCommentError(data);
            } else if (data.command === 'VIDEO_STREAM_READY' && data.widgetId === this.widgetId) {
                this.handleVideoStreamReady(data);
            } else if (data.command === 'VIDEO_STREAM_UNSUPPORTED' && data.widgetId === this.widgetId) {
                if (!data.videoPath || data.videoPath === this.currentEpisode.path) {
                    this.handleUnsupportedVideoStream(data);
                }
            } else if (data.command === 'VIDEO_STREAM_ENDED' && data.widgetId === this.widgetId) {
                if (data.streamId === this.activeStreamId) {
                    this.streamEnded = true;
                    this.finishMediaStreamIfPossible();
                }
            } else if (data.command === 'VIDEO_STREAM_ERROR' && data.widgetId === this.widgetId) {
                if (!this.activeStreamId || data.streamId === this.activeStreamId) {
                    this.failRemuxStream(data.error || '视频流处理失败');
                }
            }
        };

        this.binaryMessageHandler = (header, payload) => {
            if (header.type === 'VIDEO_STREAM_CHUNK'
                && header.widgetId === this.widgetId
                && header.streamId === this.activeStreamId
                && !this.streamFailed) {
                this.streamQueue.push({
                    payload: payload,
                    sequence: header.sequence,
                    segmentType: header.segmentType || 'unknown'
                });
                this.appendNextStreamChunk();
            }
        };

        if (typeof message_proc_func_list !== 'undefined') {
            message_proc_func_list.push(this.messageHandler);
        }
        if (typeof binary_message_proc_func_list !== 'undefined') {
            binary_message_proc_func_list.push(this.binaryMessageHandler);
        }

        // 引入NPlayer库
        this.loadNPlayerScripts();

        // 创建返回按钮栏
        const backButtonBar = cs_createBackButtons(container);

        // 创建可滚动的内容容器
        const scrollContainer = document.createElement('div');
        scrollContainer.style.cssText = `
            position: absolute;
            left: 0;
            width: 100%;
            height: 100%;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 20px;
            box-sizing: border-box;
        `;
        
        container.appendChild(scrollContainer);
        const disposeVerticalScrollbar = cs_beautifyVerticalScrollbar(scrollContainer);
        let disposeHorizontalScrollbar = null;

        // 创建容纳播放器和评论面板的弹性布局
        const playerLayout = document.createElement('div');
        playerLayout.style.cssText = 'display:flex;align-items:stretch;justify-content:center;gap:0;width:100%;margin:50px auto 20px;';
        scrollContainer.appendChild(playerLayout);
        this.playerLayout = playerLayout;

        // 创建播放器容器
        const playerContainer = document.createElement('div');
        playerContainer.style.cssText = 'width:80%;max-width:1000px;margin:0 auto;flex:0 0 auto;align-self:flex-start;';
        playerLayout.appendChild(playerContainer);

        const playerDiv = document.createElement('div');
        playerDiv.id = `cs_player_${Date.now()}`;
        playerDiv.style.cssText = 'position:relative;width:100%;aspect-ratio:16/9;border-radius:12px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,0.5);';
        playerContainer.appendChild(playerDiv);
        this.playerContainer = playerContainer;

        if (this.haveComment) {
            this.createCommentImagePreviewModal(container);
            this.createCommentPanel(backButtonBar);
            this.initializeCommentTemplateController();
        }

        if (this.haveEpisodeBar) {
            // 创建剧集列表容器
            const episodeBarContainer = document.createElement('div');
            episodeBarContainer.style.cssText = 'width:100%;max-width:1280px;margin:0 auto;';
            scrollContainer.appendChild(episodeBarContainer);

            const episodeBarLabel = document.createElement('div');
            episodeBarLabel.style.cssText = 'color:#aaa;font-size:14px;margin-bottom:10px;padding-left:10px;';
            episodeBarLabel.textContent = '剧集列表';
            episodeBarContainer.appendChild(episodeBarLabel);

            const episodeScrollContainer = document.createElement('div');
            episodeScrollContainer.style.cssText = 'white-space:nowrap;overflow-x:auto;overflow-y:hidden;padding:10px;border-radius:10px;background:rgba(255,255,255,0.05);';
            episodeBarContainer.appendChild(episodeScrollContainer);
            disposeHorizontalScrollbar = cs_beautifyHorizontalScrollbar(episodeScrollContainer);

            this.episodeScrollContainer = episodeScrollContainer;

            // 创建剧集按钮并自动滚动到当前剧集
            this.renderEpisodeBar();
            this.scrollToCurrentEpisode();
        }

        // 添加清理函数
        if (container.cleanFuncList) {
            container.cleanFuncList.push(() => {
                // 保存观看记录
                this.saveCurrentTime();
                this.disposeRemuxStream();
                // 销毁播放器
                if (this.player && this.player.dispose) {
                    this.player.dispose();
                }
                // 移除消息处理函数
                if (this.messageHandler && typeof message_proc_func_list !== 'undefined') {
                    const index = message_proc_func_list.indexOf(this.messageHandler);
                    if (index !== -1) {
                        message_proc_func_list.splice(index, 1);
                    }
                }
                if (this.binaryMessageHandler && typeof binary_message_proc_func_list !== 'undefined') {
                    const index = binary_message_proc_func_list.indexOf(this.binaryMessageHandler);
                    if (index !== -1) {
                        binary_message_proc_func_list.splice(index, 1);
                    }
                }
                // 清理滚动条样式、监听器和自动隐藏定时器
                disposeVerticalScrollbar();
                if (disposeHorizontalScrollbar) {
                    disposeHorizontalScrollbar();
                }
                this.disposeCommentPanel();
            });
        }

        // 保存播放器容器ID供后续使用
        this.playerContainerId = playerDiv.id;

        if (!this.currentEpisode)
        {
            console.error('当前剧集为空，不初始化播放器');
            return;
        }

        // 向后端请求视频数据（包含弹幕信息）
        this.sendCommand('GET_CS_VIDEO_DATA', {
            rootPath: this.rootPath,
            videoPath: this.currentEpisode.path
        });

    }

    /**
     * 将评论图片预览层创建在当前播放器页面中，由同源 iframe 脚本控制。
     * @param {HTMLElement} container - render() 当前使用的页面容器。
     */
    createCommentImagePreviewModal(container) {
        if (!this.haveComment || !container) return;
        const page = container.classList.contains('page') ? container : (container.closest('.page') || container);
        const modal = document.createElement('div');
        modal.className = 'cs-image-preview-modal';
        modal.id = 'cs-imagePreviewModal';
        modal.innerHTML = `
          <div class="cs-close-btn"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path d="M4.106 4.109a.625.625 0 0 1 .884 0L10 9.117l5.009-5.01a.625.625 0 1 1 .884.884L10.883 10l5.008 5.01a.625.625 0 0 1-.884.884L10 10.885l-5.009 5.007a.625.625 0 0 1-.884-.884L9.115 10 4.106 4.992a.625.625 0 0 1 0-.883z" fill="currentColor"></path></svg></div>
          <div class="cs-image-counter" id="cs-imageCounter"></div>
          <div class="cs-nav-btn cs-prev-btn" id="cs-prevBtn"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path d="M12.734 2.683a.625.625 0 0 1 0 .884L6.595 9.705a.417.417 0 0 0 0 .59l6.139 6.138a.625.625 0 0 1-.884.884L5.711 11.179a1.667 1.667 0 0 1 0-2.357l6.139-6.139a.625.625 0 0 1 .884 0z" fill="currentColor"></path></svg></div>
          <img id="cs-previewImage" src="" alt="预览图片">
          <div class="cs-nav-btn cs-next-btn" id="cs-nextBtn"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" style="transform:rotate(180deg)"><path d="M12.734 2.683a.625.625 0 0 1 0 .884L6.595 9.705a.417.417 0 0 0 0 .59l6.139 6.138a.625.625 0 0 1-.884.884L5.711 11.179a1.667 1.667 0 0 1 0-2.357l6.139-6.139a.625.625 0 0 1 .884 0z" fill="currentColor"></path></svg></div>`;
        page.appendChild(modal);
        this.commentImagePreviewModal = modal;
    }

    /**
     * 创建评论入口。收起时它位于返回按钮栏左侧，展开后会移动到播放器右侧。
     * @param {HTMLElement} backButtonBar - cs_createBackButtons() 返回的按钮栏。
     */
    createCommentPanel(backButtonBar) {
        if (!backButtonBar || !this.playerLayout || !this.playerContainer) return;

        const commentPanel = document.createElement('div');
        commentPanel.title = '显示评论';
        commentPanel.setAttribute('role', 'button');
        commentPanel.setAttribute('aria-label', '显示评论');
        commentPanel.setAttribute('tabindex', '0');
        commentPanel.style.cssText = `
            position:absolute;
            top:8px;
            right:calc(100% + 10px);
            width:40px;
            height:40px;
            border-radius:50%;
            background:#4A90D9;
            color:#fff;
            cursor:pointer;
            display:flex;
            align-items:center;
            justify-content:center;
            box-sizing:border-box;
            overflow:hidden;
            transform:none;
            transform-origin:center;
            transition:background 0.2s,transform 0.2s;
            box-shadow:0 2px 10px rgba(0,0,0,0.18);
            z-index:101;
        `;

        const commentIcon = this.createCommentSvg(24, 'currentColor');
        commentPanel.appendChild(commentIcon);

        const collapseButton = this.buildCommentPanelContent(commentPanel);

        const expandComment = () => this.setCommentExpanded(true);
        commentPanel.addEventListener('mouseenter', () => {
            if (!this.commentExpanded) {
                commentPanel.style.background = '#357ABD';
                commentPanel.style.transform = 'scale(1.05)';
            }
        });
        commentPanel.addEventListener('mouseleave', () => {
            if (!this.commentExpanded) {
                commentPanel.style.background = '#4A90D9';
                commentPanel.style.transform = 'none';
            }
        });
        commentPanel.addEventListener('click', expandComment);
        commentPanel.addEventListener('keydown', (event) => {
            if (!this.commentExpanded && (event.key === 'Enter' || event.key === ' ')) {
                event.preventDefault();
                expandComment();
            }
        });
        collapseButton.addEventListener('click', (event) => {
            event.stopPropagation();
            this.setCommentExpanded(false);
        });

        backButtonBar.appendChild(commentPanel);
        this.commentPanel = commentPanel;
        this.commentIcon = commentIcon;
        this.commentCollapseButton = collapseButton;
        this.commentBackButtonBar = backButtonBar;
        this.bindCommentPanelEvents();
        this.renderCommentPagination();
    }

    createCommentSvg(size = 18, color = 'currentColor') {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('width', String(size));
        svg.setAttribute('height', String(size));
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', color);
        svg.setAttribute('stroke-width', '2');
        svg.setAttribute('stroke-linecap', 'round');
        svg.setAttribute('stroke-linejoin', 'round');
        svg.innerHTML = '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"></path><path d="M8 9h8M8 13h5"></path>';
        return svg;
    }

    /** 将后端评论 HTML 中的所有 class/id 现场迁移到 cs-cmt-v1- 命名空间。 */
    prefixCommentElementNames(rootElement) {
        if (!rootElement) return;
        const elements = [rootElement, ...rootElement.querySelectorAll('*')];
        elements.forEach((element) => {
            if (element.classList) {
                Array.from(element.classList).forEach((className) => {
                    if (className.startsWith('cs-cmt-v1-')) return;
                    element.classList.replace(className, `cs-cmt-v1-${className}`);
                });
            }
            if (element.id && !element.id.startsWith('cs-cmt-v1-')) {
                element.id = `cs-cmt-v1-${element.id}`;
            }
        });
    }

    buildCommentPanelContent(commentPanel) {
        const content = document.createElement('div');
        content.className = 'cs-comment-content';
        content.style.cssText = 'display:none;flex-direction:column;width:100%;height:100%;min-width:0;color:#5f6472;background:#fff;opacity:0;box-sizing:border-box;transition:opacity .16s ease;';
        content.addEventListener('click', (event) => event.stopPropagation());
        content.innerHTML = `
          <style>
            @font-face{font-family:'CSCommentTotalCartoon';src:url("${CS_COMMENT_TOTAL_CARTOON_FONT_DATA_URL}") format('woff2');font-display:swap}
            .cs-image-preview-modal{display:none;position:absolute;inset:0;width:100%;height:100%;background:rgba(0,0,0,.8);z-index:1000;align-items:center;justify-content:center}
            .cs-image-preview-modal.cs-active{display:flex}.cs-image-preview-modal img{max-width:90%;max-height:90%;cursor:zoom-in;transition:transform .2s ease}.cs-image-preview-modal img.cs-zoomed{max-width:none;max-height:none;cursor:grab}.cs-image-preview-modal img.cs-zoomed:active{cursor:grabbing}
            .cs-image-preview-modal .cs-close-btn{position:absolute;top:20px;right:20px;width:40px;height:40px;background:rgba(255,255,255,.2);border-radius:50%;color:#fff;display:flex;align-items:center;justify-content:center;font-size:24px;cursor:pointer}
            .cs-image-preview-modal .cs-nav-btn{position:absolute;top:50%;transform:translateY(-50%);width:44px;height:44px;background:rgba(255,255,255,.2);border-radius:50%;color:#fff;display:flex;align-items:center;justify-content:center;font-size:28px;cursor:pointer;user-select:none}.cs-image-preview-modal .cs-nav-btn:hover{background:rgba(255,255,255,.4)}.cs-image-preview-modal .cs-nav-btn.cs-disabled{opacity:.3;cursor:not-allowed}.cs-image-preview-modal .cs-nav-btn.cs-disabled:hover{background:rgba(255,255,255,.2)}.cs-image-preview-modal .cs-prev-btn{left:20px}.cs-image-preview-modal .cs-next-btn{right:20px}
            .cs-image-preview-modal .cs-image-counter{position:absolute;top:20px;left:20px;font-family:"HarmonyOS_Regular";font-size:16px;color:#fff;background:rgba(0,0,0,.5);padding:6px 12px;border-radius:4px}
            .cs-cm-header{position:relative;display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:7px;padding:10px;border-bottom:1px solid #f2e8ee;background:#fffafd;flex:0 0 auto;box-sizing:border-box}
            .cs-cm-box{height:38px;display:flex;align-items:center;gap:6px;border:1px solid #f0dce6;border-radius:10px;background:#fff;box-sizing:border-box;box-shadow:0 2px 8px rgba(208,132,168,.08)}
            .cs-cm-total{padding:0 7px 0 10px;white-space:nowrap}.cs-cm-total-text{display:inline-block;transform:translateY(-5px);font-size:13px;color:#96909a}.cs-cm-total-number{font-family:'CSCommentTotalCartoon',sans-serif;font-size:34px;color:#ff69b4;vertical-align:-2px;margin:0 2px}
            .cs-cm-collapse{display:none;height:30px;padding:0 10px;border:0;border-radius:8px;background:#4a90d9;color:#fff;cursor:pointer;font-size:14px;white-space:nowrap}
            .cs-cm-source{min-width:0;padding:0 5px 0 8px}.cs-cm-source-count{display:flex;align-items:center;gap:3px;color:#d995ae;font-size:15px;white-space:nowrap;flex:0 0 auto}
            .cs-cm-source-select{position:relative;min-width:0;flex:1}.cs-cm-source-button{width:100%;height:30px;display:flex;align-items:center;justify-content:space-between;gap:4px;padding:0 7px;border:0;border-radius:7px;background:#fff5f8;color:#68636d;cursor:pointer;font-size:15px;min-width:0}
            .cs-cm-source-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}.cs-cm-source-menu{display:none;position:absolute;top:33px;left:0;right:0;max-height:210px;overflow:auto;padding:5px;background:#fff;border:1px solid #efdce5;border-radius:9px;box-shadow:0 10px 24px rgba(93,62,79,.16);z-index:30}
            .cs-cm-icon-button{border:0;border-radius:7px;cursor:pointer;display:flex;align-items:center;justify-content:center}.cs-cm-info-button{width:29px;height:30px;background:#f8edf2;color:#a8758b;font-weight:700;font-size:15px}.cs-cm-options-button{height:38px;padding:0 10px;border:1px solid #dce8f4;border-radius:10px;background:#c8dcff;color:#6489aa;cursor:pointer;font-size:15px}
            .cs-cm-popover{display:none;position:absolute;top:56px;left:10px;right:10px;padding:10px;border-radius:11px;background:rgba(255,252,253,.98);box-shadow:0 12px 30px rgba(87,58,74,.17);z-index:26}.cs-cm-source-info{border:1px solid #efdce5;font-size:15px;line-height:1.75;color:#68636d}
            .cs-cm-source-name-row{display:flex;align-items:center;min-width:0;gap:7px}.cs-cm-source-name-value{min-width:0;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.cs-cm-source-name-input{height:28px;min-width:0;flex:1;padding:0 7px;border:1px solid #d9e6f1;border-radius:7px;box-sizing:border-box;color:#626a76;font-size:15px;outline:none}.cs-cm-source-name-edit{height:27px;padding:0 9px;border:0;border-radius:7px;background:#dcecff;color:#5680a5;cursor:pointer;font-size:14px;white-space:nowrap}.cs-cm-source-name-edit:disabled{cursor:default;opacity:.6}
            .cs-cm-options{border:1px solid #dfe9f2;background:rgba(250,253,255,.98);z-index:25}.cs-cm-options-row{display:grid;grid-template-columns:auto 100px minmax(90px,1fr) 34px;gap:7px;align-items:center;font-size:15px}.cs-cm-field{height:34px;min-width:0;border:1px solid #dce7f0;border-radius:8px;background:#fff;color:#626a76;padding:0 7px;outline:none;box-sizing:border-box;font-size:15px}
            .cs-cmt-v1-comment-list .cs-cmt-v1-comment-item.cs-cmt-v1-deleted-data,.cs-cmt-v1-comment-list .cs-cmt-v1-reply-item.cs-cmt-v1-deleted-data{background-color:#fff0f5!important}
            .cs-cm-settings-button{width:34px;height:34px;background:#eaf3fa;color:#718fa8}.cs-cm-settings{display:none;margin-top:9px;padding:10px;border-top:1px solid #e5edf4;background:#f8fbfd;border-radius:0 0 9px 9px}.cs-cm-checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 10px;font-size:15px;color:#68717d}.cs-cm-checks label{display:flex;align-items:center;gap:6px;cursor:pointer}.cs-cm-checks input{accent-color:#e49bb7}.cs-cm-word{display:none;align-items:center;gap:6px;margin-top:9px;padding-top:9px;border-top:1px dashed #dbe7ef;font-size:15px;color:#717986}.cs-cm-word-count-control{position:relative;display:inline-flex;width:70px;height:34px}.cs-cm-word-count-control input{width:100%}.cs-cm-word-count-menu{display:none;position:absolute;top:38px;left:0;width:100%;padding:3px;border:1px solid #dce7f0;border-radius:8px;background:#fff;box-sizing:border-box;box-shadow:0 8px 20px rgba(93,62,79,.16);z-index:40}.cs-cm-word-count-menu button{display:block;width:100%;height:30px;border:0;border-radius:5px;background:#fff;color:#626a76;cursor:pointer;font-size:15px}.cs-cm-word-count-menu button:hover{background:#eef6fc}
            .cs-cm-scroll{display:flex;flex-direction:column;width:100%;min-height:0;flex:1 1 auto;overflow-y:auto;background:#fff;box-sizing:border-box}.cs-cm-footer{position:relative;display:flex;align-items:center;gap:8px;min-height:50px;padding:7px 10px;border-top:1px solid #f0e7ec;background:#fffafd;box-sizing:border-box;flex:0 0 auto}.cs-cm-pagination{display:flex;align-items:center;gap:5px;min-width:0;flex:1 1 auto;overflow:hidden}.cs-cm-page-size{display:flex;align-items:center;gap:5px;color:#8a848d;font-size:15px;white-space:nowrap}.cs-cm-page-size-control{position:relative;display:inline-flex;width:36px;height:30px}.cs-cm-page-size input{width:100%;height:30px;border:1px solid #efdce5;border-radius:7px;padding:0 3px;color:#726b75;background:#fff;box-sizing:border-box;font-size:15px}.cs-cm-page-size-menu{display:none;position:absolute;left:0;bottom:34px;width:100%;padding:3px;border:1px solid #efdce5;border-radius:7px;background:#fff;box-sizing:border-box;box-shadow:0 8px 20px rgba(93,62,79,.16);z-index:40}.cs-cm-page-size-menu button{display:block;width:100%;height:30px;border:0;border-radius:5px;background:#fff;color:#726b75;cursor:pointer;font-size:15px}.cs-cm-page-size-menu button:hover{background:#fff1f6}
          </style>
          <div class="cs-cm-header">
            <div class="cs-cm-box cs-cm-total"><span class="cs-cm-total-text">共 <span class="cs-cm-total-number">0</span> 条评论</span><button class="cs-cm-collapse" type="button">收起</button></div>
            <div class="cs-cm-box cs-cm-source">
              <span class="cs-cm-source-count"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#e7a8be" stroke-width="2"><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"></path><path d="M8 9h8M8 13h5"></path></svg><span>0</span></span>
              <div class="cs-cm-source-select"><button class="cs-cm-source-button" type="button"><span class="cs-cm-source-label">暂无来源</span><span>▾</span></button><div class="cs-cm-source-menu"></div></div>
              <button class="cs-cm-icon-button cs-cm-info-button" type="button" title="来源详情">...</button>
            </div>
            <button class="cs-cm-options-button" type="button">选项</button>
            <div class="cs-cm-popover cs-cm-source-info"></div>
            <div class="cs-cm-popover cs-cm-options">
              <div class="cs-cm-options-row"><span>排序方式</span><select class="cs-cm-field cs-cm-sort"><option value="time">按时间</option><option value="like">按热度</option></select><input class="cs-cm-field cs-cm-keyword" type="search" placeholder="关键词筛选"><button class="cs-cm-icon-button cs-cm-settings-button" type="button" title="筛选设置"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg></button></div>
              <div class="cs-cm-settings"><div class="cs-cm-checks"><label><input data-comment-setting="markDeleted" type="checkbox">标识被删掉的数据</label><label><input data-comment-setting="onlyDeleted" type="checkbox">只显示被删数据</label><label><input data-comment-setting="onlyVip" type="checkbox">只显示大会员评论</label><label><input data-comment-setting="wordFilterEnabled" type="checkbox">字数筛选</label></div><div class="cs-cm-word">只显示 <span class="cs-cm-word-count-control"><input class="cs-cm-field cs-cm-word-count" type="text" inputmode="numeric" pattern="[0-9]*" value="0"><span class="cs-cm-word-count-menu"><button type="button" data-word-count="20">20</button><button type="button" data-word-count="50">50</button><button type="button" data-word-count="100">100</button><button type="button" data-word-count="200">200</button></span></span><select class="cs-cm-field cs-cm-word-direction"><option value="above">字以上</option><option value="below">字以下</option></select> 的评论</div></div>
            </div>
          </div>`;

        const scrollContainer = document.createElement('div');
        scrollContainer.className = 'cs-cm-scroll';
        scrollContainer.setAttribute('role', 'region');
        scrollContainer.setAttribute('aria-label', '评论内容');
        const templateDocument = new DOMParser().parseFromString(
            String(this.commentTemplate || ''),
            'text/html'
        );
        const templateStyle = templateDocument.querySelector('style');
        const commentRoot = document.createElement('div');
        commentRoot.className = 'cs-cmt-v1-root';
        const commentStyle = document.createElement('style');
        commentStyle.textContent = String(
            templateStyle ? templateStyle.textContent : ''
        );
        const commentList = document.createElement('div');
        commentList.className =
            'cs-cmt-v1-comment-list cs-cmt-v1-comment-list-empty';
        commentList.textContent = '正在加载评论…';
        commentRoot.append(commentStyle, commentList);
        scrollContainer.appendChild(commentRoot);
        content.appendChild(scrollContainer);

        const footer = document.createElement('div');
        footer.className = 'cs-cm-footer';
        footer.innerHTML = `<div class="cs-cm-pagination"></div><label class="cs-cm-page-size">每页 <span class="cs-cm-page-size-control"><input type="text" inputmode="numeric" pattern="[0-9]*" value="20"><span class="cs-cm-page-size-menu"><button type="button" data-page-size="5">5</button><button type="button" data-page-size="10">10</button><button type="button" data-page-size="20">20</button></span></span> 条评论</label>`;
        content.appendChild(footer);
        commentPanel.appendChild(content);

        const find = (selector) => content.querySelector(selector);
        this.commentContent = content;
        this.commentScrollContainer = scrollContainer;
        this.commentRoot = commentRoot;
        this.commentList = commentList;
        this.commentScrollbarCleanup = cs_beautifyScrollbar(scrollContainer, 'vertical');
        this.commentTotalNumber = find('.cs-cm-total-number');
        this.commentSourceCount = find('.cs-cm-source-count span');
        this.commentSourceButton = find('.cs-cm-source-button');
        this.commentSourceButtonLabel = find('.cs-cm-source-label');
        this.commentSourceMenu = find('.cs-cm-source-menu');
        this.commentSourceInfoPopover = find('.cs-cm-source-info');
        this.commentOptionsPopover = find('.cs-cm-options');
        this.commentSettingsPopover = find('.cs-cm-settings');
        this.commentPagination = find('.cs-cm-pagination');
        this.commentPageSizeInput = find('.cs-cm-page-size input');
        this.commentPageSizeMenu = find('.cs-cm-page-size-menu');
        this.commentSortSelect = find('.cs-cm-sort');
        this.commentKeywordInput = find('.cs-cm-keyword');
        this.commentMarkDeletedInput = find('[data-comment-setting="markDeleted"]');
        this.commentOnlyDeletedInput = find('[data-comment-setting="onlyDeleted"]');
        this.commentOnlyVipInput = find('[data-comment-setting="onlyVip"]');
        this.commentWordFilterInput = find('[data-comment-setting="wordFilterEnabled"]');
        this.commentWordControls = find('.cs-cm-word');
        this.commentWordCountInput = find('.cs-cm-word-count');
        this.commentWordCountMenu = find('.cs-cm-word-count-menu');
        this.commentWordDirectionSelect = find('.cs-cm-word-direction');
        this.commentSourceInfoButton = find('.cs-cm-info-button');
        this.commentOptionsButton = find('.cs-cm-options-button');
        this.commentSettingsButton = find('.cs-cm-settings-button');
        return find('.cs-cm-collapse');
    }

    resetCommentContent(emptyText = '正在加载评论…') {
        this.setCommentContent('', emptyText);
    }

    setCommentContent(htmlText, emptyText = '', perfStep = null) {
        if (!this.commentList) return;
        if (this.commentFontStyleElement) {
            this.commentFontStyleElement.remove();
            this.commentFontStyleElement = null;
        }
        if (htmlText) {
            this.commentList.classList.remove('cs-cmt-v1-comment-list-empty');
            this.commentList.innerHTML = htmlText;
            //[DEBUG-START] 性能调试代码，release时删掉
            if (perfStep) perfStep('innerHTML 解析及插入');
            //[DEBUG-END]
            this.normalizeCommentContentActions();
            //[DEBUG-START] 性能调试代码，release时删掉
            if (perfStep) perfStep('评论事件属性转换');
            //[DEBUG-END]
            const fontStyles = Array.from(this.commentList.querySelectorAll('style'))
                .filter((style) => style.textContent.includes('@font-face'));
            if (fontStyles.length) {
                this.commentFontStyleElement = document.createElement('style');
                this.commentFontStyleElement.dataset.csCommentFontOwner = this.widgetId;
                this.commentFontStyleElement.textContent = fontStyles
                    .map((style) => style.textContent)
                    .join('\n');
                document.head.appendChild(this.commentFontStyleElement);
                fontStyles.forEach((style) => style.remove());
            }
            this.prefixCommentElementNames(this.commentList);
            //[DEBUG-START] 性能调试代码，release时删掉
            if (perfStep) perfStep('字体样式迁移及 class/id 处理');
            //[DEBUG-END]
        } else {
            this.commentList.classList.add('cs-cmt-v1-comment-list-empty');
            this.commentList.textContent = emptyText || '暂无评论';
        }
        if (this.commentScrollContainer) {
            this.commentScrollContainer.scrollTop = 0;
        }
        //[DEBUG-START] 性能调试代码，release时删掉
        if (perfStep) perfStep('重置滚动位置（可能触发布局计算）');
        //[DEBUG-END]
    }

    /** 将旧后端进程生成的内联事件转换成普通评论根 div 事件代理使用的 data 属性。 */
    normalizeCommentContentActions() {
        if (!this.commentList) return;
        this.commentList.querySelectorAll('[onclick]').forEach((element) => {
            const source = String(element.getAttribute('onclick') || '').trim();
            let match = source.match(/^toggleReplies\((\d+),\s*(\d+)\)$/);
            if (match) {
                element.dataset.csCmtAction = 'toggle-replies';
                element.dataset.commentId = match[1];
                element.dataset.totalCount = match[2];
                element.removeAttribute('onclick');
                return;
            }
            match = source.match(/^showReplyPage\((\d+),\s*(\d+),\s*(\d+)\)$/);
            if (match) {
                element.dataset.csCmtAction = 'reply-page';
                element.dataset.commentId = match[1];
                element.dataset.page = match[2];
                element.dataset.totalCount = match[3];
                element.removeAttribute('onclick');
                return;
            }
            if (source.startsWith('previewImage(')) {
                element.setAttribute('data-cs-cmt-preview', '');
                element.removeAttribute('onclick');
            }
        });
    }

    /** 在 render() 的 haveComment 分支中初始化原评论模板脚本提供的交互。 */
    initializeCommentTemplateController() {
        if (!this.commentRoot || !this.commentImagePreviewModal) return;

        this.commentRoot.addEventListener('click', (event) => {
            this.closeCommentPopovers();
            const target = event.composedPath().find((node) => node instanceof Element) || null;
            if (!target) return;

            const previewTrigger = target.closest('[data-cs-cmt-preview]');
            if (previewTrigger) {
                const pictureGroup = previewTrigger.closest(
                    '.cs-cmt-v1-comment-picture'
                );
                const pictures = pictureGroup
                    ? Array.from(pictureGroup.querySelectorAll('img'))
                    : [];
                const clickedImage = previewTrigger.matches('img')
                    ? previewTrigger
                    : previewTrigger.querySelector('img');
                const images = pictures.map((image) => image.src).filter(Boolean);
                const index = Math.max(0, pictures.indexOf(clickedImage));
                if (images.length) this.previewCommentImages(images, index);
                return;
            }

            const actionElement = target.closest('[data-cs-cmt-action]');
            if (!actionElement) return;
            // data-comment-id 保存的是业务 rpid，不属于 DOM 命名空间。兼容曾经
            // 错误输出为 cs-cmt-v1-<rpid> 的旧后端响应，避免节点 ID 被重复加前缀。
            const commentId = String(actionElement.dataset.commentId || '')
                .replace(/^cs-cmt-v1-/, '');
            if (!commentId) return;
            const totalCount = Math.max(0, Number(actionElement.dataset.totalCount) || 0);
            if (actionElement.dataset.csCmtAction === 'toggle-replies') {
                this.toggleCommentReplies(commentId, totalCount);
            } else if (actionElement.dataset.csCmtAction === 'reply-page') {
                this.showCommentReplyPage(
                    commentId,
                    Math.max(1, Number(actionElement.dataset.page) || 1),
                    totalCount
                );
            }
        });

        const modal = this.commentImagePreviewModal;
        const image = modal.querySelector('#cs-previewImage');
        const closeButton = modal.querySelector('.cs-close-btn');
        const previousButton = modal.querySelector('#cs-prevBtn');
        const nextButton = modal.querySelector('#cs-nextBtn');

        image.onclick = (event) => {
            event.stopPropagation();
            if (this.commentPreviewDragMoved) {
                this.commentPreviewDragMoved = false;
                return;
            }
            this.commentPreviewZoomed = !this.commentPreviewZoomed;
            image.classList.toggle('cs-zoomed', this.commentPreviewZoomed);
            if (!this.commentPreviewZoomed) {
                this.commentPreviewTranslateX = 0;
                this.commentPreviewTranslateY = 0;
                image.style.transform = 'translate(0, 0)';
            }
        };
        image.onmousedown = (event) => {
            if (!this.commentPreviewZoomed) return;
            event.preventDefault();
            this.commentPreviewDragging = true;
            this.commentPreviewDragMoved = false;
            this.commentPreviewStartX = event.clientX - this.commentPreviewTranslateX;
            this.commentPreviewStartY = event.clientY - this.commentPreviewTranslateY;
        };
        modal.onmousemove = (event) => {
            if (!this.commentPreviewZoomed || !this.commentPreviewDragging) return;
            this.commentPreviewDragMoved = true;
            this.commentPreviewTranslateX = event.clientX - this.commentPreviewStartX;
            this.commentPreviewTranslateY = event.clientY - this.commentPreviewStartY;
            image.style.transform = `translate(${this.commentPreviewTranslateX}px, ${this.commentPreviewTranslateY}px)`;
        };
        modal.onmouseup = () => {
            this.commentPreviewDragging = false;
        };
        modal.onclick = (event) => {
            if (event.target === modal) this.closeCommentImagePreview();
        };
        closeButton.onclick = (event) => {
            event.stopPropagation();
            this.closeCommentImagePreview();
        };
        previousButton.onclick = (event) => {
            event.stopPropagation();
            this.navigateCommentImagePreview(-1);
        };
        nextButton.onclick = (event) => {
            event.stopPropagation();
            this.navigateCommentImagePreview(1);
        };
    }

    previewCommentImages(images, index = 0) {
        this.commentPreviewImages = Array.isArray(images) ? images.slice() : [String(images)];
        this.commentPreviewIndex = Math.min(
            this.commentPreviewImages.length - 1,
            Math.max(0, Number(index) || 0)
        );
        this.showCurrentCommentPreviewImage();
        this.commentImagePreviewModal.classList.add('cs-active');
        this.commentImagePreviewModal.style.display = 'flex';
        if (this.commentImagePreviewModal.parentElement) {
            this.commentImagePreviewModal.parentElement.style.overflow = 'hidden';
        }
    }

    showCurrentCommentPreviewImage() {
        const modal = this.commentImagePreviewModal;
        if (!modal || !this.commentPreviewImages.length) return;
        const image = modal.querySelector('#cs-previewImage');
        const counter = modal.querySelector('#cs-imageCounter');
        const previousButton = modal.querySelector('#cs-prevBtn');
        const nextButton = modal.querySelector('#cs-nextBtn');
        image.src = this.commentPreviewImages[this.commentPreviewIndex];
        image.classList.remove('cs-zoomed');
        image.style.transform = 'translate(0, 0)';
        this.commentPreviewZoomed = false;
        this.commentPreviewDragging = false;
        this.commentPreviewDragMoved = false;
        this.commentPreviewTranslateX = 0;
        this.commentPreviewTranslateY = 0;
        counter.textContent = this.commentPreviewImages.length > 1
            ? `${this.commentPreviewIndex + 1} / ${this.commentPreviewImages.length}`
            : '';
        previousButton.classList.toggle('cs-disabled', this.commentPreviewIndex <= 0);
        nextButton.classList.toggle(
            'cs-disabled',
            this.commentPreviewIndex >= this.commentPreviewImages.length - 1
        );
    }

    navigateCommentImagePreview(direction) {
        const nextIndex = this.commentPreviewIndex + direction;
        if (nextIndex < 0 || nextIndex >= this.commentPreviewImages.length) return;
        this.commentPreviewIndex = nextIndex;
        this.showCurrentCommentPreviewImage();
    }

    closeCommentImagePreview() {
        if (!this.commentImagePreviewModal) return;
        this.commentImagePreviewModal.classList.remove('cs-active');
        this.commentImagePreviewModal.style.display = 'none';
        if (this.commentImagePreviewModal.parentElement) {
            this.commentImagePreviewModal.parentElement.style.overflow = '';
        }
    }

    toggleCommentReplies(commentId, totalCount) {
        if (!this.commentRoot) return;
        const container = this.commentRoot.querySelector(
            `#cs-cmt-v1-reply-container-${commentId}`
        );
        if (!container) return;
        const expandButton = container.nextElementSibling
            && container.nextElementSibling.classList.contains(
                'cs-cmt-v1-reply-expand-btn'
            )
            ? container.nextElementSibling
            : null;
        const pagination = this.commentRoot.querySelector(
            `#cs-cmt-v1-reply-pagination-${commentId}`
        );
        const items = container.querySelectorAll('.cs-cmt-v1-reply-item');
        const isCollapsed = expandButton && expandButton.style.display !== 'none';

        if (isCollapsed) {
            const showCount = Math.min(totalCount, 5);
            items.forEach((item, index) => {
                item.style.display = index < showCount ? '' : 'none';
            });
            expandButton.style.display = 'none';
            if (pagination && totalCount > 5) {
                pagination.style.display = '';
                this.updateCommentReplyPagination(commentId, 1, totalCount);
            }
        } else {
            items.forEach((item, index) => {
                item.style.display = index < 2 ? '' : 'none';
            });
            if (expandButton) expandButton.style.display = '';
            if (pagination) pagination.style.display = 'none';
        }
    }

    showCommentReplyPage(commentId, pageNumber, totalCount) {
        if (!this.commentRoot) return;
        const container = this.commentRoot.querySelector(
            `#cs-cmt-v1-reply-container-${commentId}`
        );
        if (!container) return;
        const startIndex = (pageNumber - 1) * 5;
        const endIndex = startIndex + 5;
        container.querySelectorAll('.cs-cmt-v1-reply-item').forEach((item, index) => {
            item.style.display = index >= startIndex && index < endIndex ? '' : 'none';
        });
        this.updateCommentReplyPagination(commentId, pageNumber, totalCount);
    }

    updateCommentReplyPagination(commentId, currentPage, totalCount) {
        if (!this.commentRoot) return;
        const pagination = this.commentRoot.querySelector(
            `#cs-cmt-v1-reply-pagination-${commentId}`
        );
        if (!pagination) return;
        const totalPages = Math.ceil(totalCount / 5);
        const pageButton = (
            page,
            text,
            className = 'cs-cmt-v1-page-num'
        ) => `<span class="${className}${page === currentPage ? ' cs-cmt-v1-active' : ''}" data-cs-cmt-action="reply-page" data-comment-id="${commentId}" data-page="${page}" data-total-count="${totalCount}">${text}</span>`;
        let html = `<span class="cs-cmt-v1-page-count">共${totalPages}页</span>`;

        if (currentPage > 1) {
            html += pageButton(currentPage - 1, '上一页', 'cs-cmt-v1-page-btn');
        }
        if (totalPages <= 6) {
            for (let page = 1; page <= totalPages; page++) {
                html += pageButton(page, String(page));
            }
        } else if (currentPage <= 3) {
            for (let page = 1; page <= 5; page++) {
                html += pageButton(page, String(page));
            }
            html += '<span class="cs-cmt-v1-page-ellipsis">...</span>';
            html += pageButton(totalPages, String(totalPages));
        } else if (currentPage >= totalPages - 2) {
            html += pageButton(1, '1');
            html += '<span class="cs-cmt-v1-page-ellipsis">...</span>';
            for (let page = totalPages - 4; page <= totalPages; page++) {
                html += pageButton(page, String(page));
            }
        } else {
            html += pageButton(1, '1');
            html += '<span class="cs-cmt-v1-page-ellipsis">...</span>';
            for (let page = currentPage - 2; page <= currentPage + 2; page++) {
                html += pageButton(page, String(page));
            }
            html += '<span class="cs-cmt-v1-page-ellipsis">...</span>';
            html += pageButton(totalPages, String(totalPages));
        }
        if (currentPage < totalPages) {
            html += pageButton(currentPage + 1, '下一页', 'cs-cmt-v1-page-btn');
        }
        html += `<span class="cs-cmt-v1-page-btn" data-cs-cmt-action="toggle-replies" data-comment-id="${commentId}" data-total-count="${totalCount}">收起</span>`;
        pagination.innerHTML = html;
    }

    closeCommentPopovers() {
        [this.commentSourceMenu, this.commentSourceInfoPopover,
            this.commentOptionsPopover, this.commentSettingsPopover,
            this.commentPageSizeMenu, this.commentWordCountMenu].forEach((element) => {
            if (element) element.style.display = 'none';
        });
    }

    bindCommentPanelEvents() {
        const toggleSingle = (target) => {
            const opening = target && getComputedStyle(target).display === 'none';
            this.closeCommentPopovers();
            if (opening) target.style.display = 'block';
        };
        this.commentSourceButton.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleSingle(this.commentSourceMenu);
        });
        this.commentSourceInfoButton.addEventListener('click', (event) => {
            event.stopPropagation();
            const opening = this.commentSourceInfoPopover.style.display === 'none';
            this.closeCommentPopovers();
            if (opening) {
                this.renderCommentSourceInfo();
                this.commentSourceInfoPopover.style.display = 'block';
            }
        });
        this.commentOptionsButton.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleSingle(this.commentOptionsPopover);
        });
        this.commentSettingsButton.addEventListener('click', (event) => {
            event.stopPropagation();
            this.commentSettingsPopover.style.display =
                this.commentSettingsPopover.style.display === 'none' ? 'block' : 'none';
        });
        this.commentSortSelect.addEventListener('change', () => {
            this.commentSettings.sortBy = this.commentSortSelect.value === 'like' ? 'like' : 'time';
            this.refreshCommentHtml(true);
        });
        this.commentKeywordInput.addEventListener('input', () => {
            clearTimeout(this.commentKeywordTimer);
            this.commentKeywordTimer = setTimeout(() => this.refreshCommentHtml(true), 320);
        });
        [this.commentMarkDeletedInput, this.commentOnlyDeletedInput,
            this.commentOnlyVipInput, this.commentWordFilterInput].forEach((input) => {
            input.addEventListener('change', () => {
                this.commentSettings[input.dataset.commentSetting] = input.checked;
                if (input === this.commentWordFilterInput) {
                    this.commentWordControls.style.display = input.checked ? 'flex' : 'none';
                }
                this.refreshCommentHtml(true);
            });
        });
        const updateWordFilter = () => {
            this.commentSettings.wordCount = Math.max(0, Number(this.commentWordCountInput.value) || 0);
            this.commentSettings.wordDirection = this.commentWordDirectionSelect.value === 'below' ? 'below' : 'above';
            if (this.commentSettings.wordFilterEnabled) this.refreshCommentHtml(true);
        };
        this.commentWordCountInput.addEventListener('change', updateWordFilter);
        this.commentWordDirectionSelect.addEventListener('change', updateWordFilter);
        const openWordCountMenu = () => {
            this.commentWordCountMenu.style.display = 'block';
        };
        this.commentWordCountInput.addEventListener('focus', openWordCountMenu);
        this.commentWordCountInput.addEventListener('click', openWordCountMenu);
        this.commentWordCountInput.addEventListener('input', () => {
            this.commentWordCountInput.value =
                this.commentWordCountInput.value.replace(/[^0-9]/g, '');
        });
        this.commentWordCountMenu.querySelectorAll('[data-word-count]').forEach((button) => {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                this.commentWordCountInput.value = button.dataset.wordCount;
                this.commentWordCountMenu.style.display = 'none';
                this.commentWordCountInput.dispatchEvent(new Event('change'));
            });
        });
        const openPageSizeMenu = () => {
            this.closeCommentPopovers();
            this.commentPageSizeMenu.style.display = 'block';
        };
        this.commentPageSizeInput.addEventListener('focus', openPageSizeMenu);
        this.commentPageSizeInput.addEventListener('click', openPageSizeMenu);
        this.commentPageSizeInput.addEventListener('input', () => {
            this.commentPageSizeInput.value =
                this.commentPageSizeInput.value.replace(/[^0-9]/g, '');
        });
        this.commentPageSizeMenu.querySelectorAll('[data-page-size]').forEach((button) => {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                this.commentPageSizeInput.value = button.dataset.pageSize;
                this.commentPageSizeMenu.style.display = 'none';
                this.commentPageSizeInput.dispatchEvent(new Event('change'));
            });
        });
        this.commentPageSizeInput.addEventListener('change', () => {
            const value = Math.min(200, Math.max(1, Number(this.commentPageSizeInput.value) || 20));
            this.commentPageSizeInput.value = String(value);
            this.commentSettings.pageSize = value;
            this.requestCommentHtml(true, true);
        });

        this.commentOutsideClickHandler = (event) => {
            const target = event.target;
            if (!this.commentPanel || !this.commentPanel.contains(target)) {
                this.closeCommentPopovers();
                return;
            }
            if (!this.commentSourceButton.contains(target)
                && !this.commentSourceMenu.contains(target)) {
                this.commentSourceMenu.style.display = 'none';
            }
            if (!this.commentSourceInfoButton.contains(target)
                && !this.commentSourceInfoPopover.contains(target)) {
                this.commentSourceInfoPopover.style.display = 'none';
            }
            if (!this.commentOptionsButton.contains(target)
                && !this.commentOptionsPopover.contains(target)) {
                this.commentOptionsPopover.style.display = 'none';
                this.commentSettingsPopover.style.display = 'none';
            }
            if (target !== this.commentPageSizeInput
                && !this.commentPageSizeMenu.contains(target)) {
                this.commentPageSizeMenu.style.display = 'none';
            }
            if (target !== this.commentWordCountInput
                && !this.commentWordCountMenu.contains(target)) {
                this.commentWordCountMenu.style.display = 'none';
            }
        };
        document.addEventListener('pointerdown', this.commentOutsideClickHandler, true);
        this.commentScrollContainer.addEventListener(
            'pointerdown',
            () => this.closeCommentPopovers()
        );
    }

    currentCommentMetadataPath() {
        if (!this.currentEpisode) return '';
        const path = String(this.currentEpisode.path || '');
        const root = String(this.rootPath || '').replace(/[\\/]+$/, '');
        const separator = root.includes('\\') ? '\\' : '/';
        return `${root}${separator}${path}@meta`;
    }

    commentResourcePath(source) {
        const databasePath = String(source && source.databasePath || '');
        const slashIndex = Math.max(
            databasePath.lastIndexOf('/'),
            databasePath.lastIndexOf('\\')
        );
        const commentDirectory = slashIndex >= 0
            ? databasePath.slice(0, slashIndex)
            : '';
        const resourceFolder = String(
            source && source['resource-folder'] || ''
        ).trim();
        if (!resourceFolder) return commentDirectory;
        const isAbsolute = /^[A-Za-z]:[\\/]/.test(resourceFolder)
            || resourceFolder.startsWith('\\\\')
            || resourceFolder.startsWith('/');
        if (isAbsolute) return resourceFolder;
        const separator = databasePath.includes('\\') ? '\\' : '/';
        const relativeFolder = resourceFolder.replace(/^[.][\\/]/, '');
        return `${commentDirectory}${separator}${relativeFolder}`;
    }

    resetCommentPanelForEpisode(requestImmediately = false) {
        this.commentInfoRequestId = '';
        this.commentHtmlRequestId = '';
        this.commentSourceInfoRequestId = '';
        this.commentSourceInfoPending = null;
        this.commentInfo = null;
        this.commentSources = [];
        this.commentCurrentSource = null;
        this.commentCurrentPage = 1;
        this.commentTotalPages = 1;
        this.commentFilteredCount = 0;
        clearTimeout(this.commentKeywordTimer);
        this.commentKeywordTimer = null;
        if (this.commentKeywordInput) this.commentKeywordInput.value = '';
        if (this.commentTotalNumber) this.commentTotalNumber.textContent = '0';
        if (this.commentSourceCount) this.commentSourceCount.textContent = '0';
        if (this.commentSourceButtonLabel) this.commentSourceButtonLabel.textContent = '暂无来源';
        if (this.commentSourceMenu) this.commentSourceMenu.innerHTML = '';
        this.renderCommentPagination();
        this.resetCommentContent('正在读取评论信息…');
        if (requestImmediately && this.commentExpanded) this.requestCommentInfo();
    }

    requestCommentInfo() {
        if (!this.commentExpanded || !this.currentEpisode) return;
        const requestId = `${this.widgetId}_comment_info_${++this.commentRequestSerial}`;
        this.commentInfoRequestId = requestId;
        this.setCommentContent('', '正在读取评论信息…');
        this.sendCommand('CS_GET_COMMENT_INFO', {
            requestId,
            metadataPath: this.currentCommentMetadataPath()
        });
    }

    handleCommentInfo(data) {
        if (!this.commentExpanded || data.requestId !== this.commentInfoRequestId) return;
        this.commentInfo = data;
        this.commentSources = Array.isArray(data.sources) ? data.sources : [];
        if (this.commentTotalNumber) {
            this.commentTotalNumber.textContent = String(Number(data.totalCount) || 0);
        }
        const config = data.config || {};
        const record = data.record || {};
        const globalPageSize = Math.min(
            200,
            Math.max(1, Number(config['page-size']) || 20)
        );
        const recordedPageSize = Number(record['last-pagecount']);
        this.commentSettings = {
            pageSize: Number.isFinite(recordedPageSize) && recordedPageSize > 0
                ? Math.min(200, Math.max(1, recordedPageSize))
                : globalPageSize,
            sortBy: config['sort-by'] === 'like' ? 'like' : 'time',
            markDeleted: Boolean(config['mark-deleted']),
            onlyDeleted: Boolean(config['only-deleted']),
            onlyVip: Boolean(config['only-vip']),
            wordFilterEnabled: Boolean(config['word-filter-enabled']),
            wordCount: Math.max(0, Number(config['word-count']) || 0),
            wordDirection: config['word-direction'] === 'below' ? 'below' : 'above'
        };
        this.syncCommentSettingControls();
        this.renderCommentSourceMenu();
        if (!this.commentSources.length) {
            this.commentCurrentSource = null;
            this.resetCommentContent('该视频暂无评论数据');
            this.renderCommentPagination();
            return;
        }
        const rememberedBvid = record['last-read-src-BV'];
        const source = this.commentSources.find((item) => item.bvid === rememberedBvid)
            || this.commentSources[0];
        const rememberedPage = Math.max(1, Number(record['last-read-page']) || 1);
        this.selectCommentSource(source, rememberedPage, true);
    }

    syncCommentSettingControls() {
        if (!this.commentSortSelect) return;
        this.commentSortSelect.value = this.commentSettings.sortBy;
        this.commentPageSizeInput.value = String(this.commentSettings.pageSize);
        this.commentMarkDeletedInput.checked = this.commentSettings.markDeleted;
        this.commentOnlyDeletedInput.checked = this.commentSettings.onlyDeleted;
        this.commentOnlyVipInput.checked = this.commentSettings.onlyVip;
        this.commentWordFilterInput.checked = this.commentSettings.wordFilterEnabled;
        this.commentWordCountInput.value = String(this.commentSettings.wordCount);
        this.commentWordDirectionSelect.value = this.commentSettings.wordDirection;
        this.commentWordControls.style.display = this.commentSettings.wordFilterEnabled ? 'flex' : 'none';
    }

    renderCommentSourceMenu() {
        if (!this.commentSourceMenu) return;
        this.commentSourceMenu.innerHTML = '';
        this.commentSources.forEach((source) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.style.cssText = 'width:100%;height:38px;display:flex;align-items:center;gap:7px;padding:0 7px;border:0;border-radius:7px;background:transparent;color:#68636d;cursor:pointer;font-size:15px;text-align:left;';
            button.onmouseenter = () => { button.style.background = '#fff1f6'; };
            button.onmouseleave = () => { button.style.background = 'transparent'; };
            const name = document.createElement('span');
            name.textContent = source.sourceName || source.bvid || '未命名来源';
            name.title = name.textContent;
            name.style.cssText = 'min-width:0;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
            const count = document.createElement('span');
            count.style.cssText = 'display:flex;align-items:center;gap:3px;color:#c98ba3;white-space:nowrap;flex:0 0 auto;';
            count.append(
                this.createCommentSvg(13, '#e1a2ba'),
                document.createTextNode(String(Number(source.commentCount) || 0))
            );
            button.append(name, count);
            button.addEventListener('click', () => {
                this.selectCommentSource(source, 1);
                this.closeCommentPopovers();
            });
            this.commentSourceMenu.appendChild(button);
        });
    }

    selectCommentSource(source, page = 1, force = false) {
        if (!source || (!force && this.commentCurrentSource === source)) return;
        this.commentCurrentSource = source;
        this.resetCommentContent('正在加载评论…');
        this.commentCurrentPage = Math.max(1, Number(page) || 1);
        this.commentFilteredCount = Number(source.commentCount) || 0;
        this.commentTotalPages = Math.max(
            1, Math.ceil(this.commentFilteredCount / this.commentSettings.pageSize)
        );
        if (this.commentSourceButtonLabel) {
            this.commentSourceButtonLabel.textContent =
                source.sourceName || source.bvid || '未命名来源';
            this.commentSourceButtonLabel.title = this.commentSourceButtonLabel.textContent;
        }
        if (this.commentSourceCount) {
            this.commentSourceCount.textContent = String(Number(source.commentCount) || 0);
        }
        this.renderCommentSourceInfo();
        this.renderCommentPagination();
        this.requestCommentHtml(!force);
    }

    renderCommentSourceInfo() {
        const popover = this.commentSourceInfoPopover;
        if (!popover) return;
        popover.replaceChildren();
        const source = this.commentCurrentSource;
        if (!source) {
            popover.textContent = '暂无评论来源信息';
            return;
        }
        const grid = document.createElement('div');
        grid.style.cssText = 'display:grid;grid-template-columns:auto minmax(0,1fr);gap:3px 10px;';
        const addRow = (label, value, title = '') => {
            const labelElement = document.createElement('span');
            labelElement.textContent = label;
            labelElement.style.color = '#a49ca5';
            const valueElement = value instanceof Node ? value : document.createElement('span');
            if (!(value instanceof Node)) valueElement.textContent = String(value);
            valueElement.style.overflow = 'hidden';
            valueElement.style.textOverflow = 'ellipsis';
            valueElement.style.whiteSpace = 'nowrap';
            if (title) valueElement.title = title;
            grid.append(labelElement, valueElement);
        };
        const sourceNameRow = document.createElement('span');
        sourceNameRow.className = 'cs-cm-source-name-row';
        const sourceNameValue = document.createElement('span');
        sourceNameValue.className = 'cs-cm-source-name-value';
        sourceNameValue.textContent = source.sourceName || source.bvid || '未知';
        sourceNameValue.title = sourceNameValue.textContent;
        const sourceNameInput = document.createElement('input');
        sourceNameInput.className = 'cs-cm-source-name-input';
        sourceNameInput.type = 'text';
        sourceNameInput.maxLength = 200;
        sourceNameInput.value = sourceNameValue.textContent;
        sourceNameInput.style.display = 'none';
        const sourceNameEdit = document.createElement('button');
        sourceNameEdit.className = 'cs-cm-source-name-edit';
        sourceNameEdit.type = 'button';
        sourceNameEdit.textContent = '编辑';
        let editingSourceName = false;
        const setEditingSourceName = (editing) => {
            editingSourceName = editing;
            sourceNameValue.style.display = editing ? 'none' : '';
            sourceNameInput.style.display = editing ? '' : 'none';
            sourceNameEdit.textContent = editing ? '确定' : '编辑';
            if (editing) {
                sourceNameInput.value = source.sourceName || source.bvid || '';
                sourceNameInput.focus();
                sourceNameInput.select();
            }
        };
        sourceNameEdit.addEventListener('click', () => {
            if (!editingSourceName) {
                setEditingSourceName(true);
                return;
            }
            const nextName = sourceNameInput.value.trim();
            if (!nextName) {
                sourceNameInput.focus();
                return;
            }
            const previousName = source.sourceName || source.bvid || '未知';
            setEditingSourceName(false);
            if (nextName === previousName) return;

            const requestId =
                `${this.widgetId}_comment_source_info_${++this.commentRequestSerial}`;
            this.commentSourceInfoRequestId = requestId;
            this.commentSourceInfoPending = {
                requestId,
                source,
                previousName,
                editButton: sourceNameEdit
            };
            source.sourceName = nextName;
            sourceNameValue.textContent = nextName;
            sourceNameValue.title = nextName;
            sourceNameEdit.disabled = true;
            this.updateDisplayedCommentSourceName(source);
            const sent = this.sendCommand('CS_SET_COMMENT_SOURCEINFO', {
                requestId,
                cmListPath: this.commentInfo && this.commentInfo.cmListPath || '',
                bvid: source.bvid || '',
                key: 'src-name',
                value: nextName
            });
            if (sent === false) {
                this.handleCommentError({
                    stage: 'source-info',
                    requestId,
                    error: 'WebSocket 未连接，评论来源名称未保存'
                });
            }
        });
        sourceNameInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                sourceNameEdit.click();
            } else if (event.key === 'Escape') {
                event.preventDefault();
                setEditingSourceName(false);
            }
        });
        sourceNameRow.append(sourceNameValue, sourceNameInput, sourceNameEdit);
        addRow('来源', sourceNameRow);
        if (source.bvid) {
            const link = document.createElement('a');
            link.href = `https://www.bilibili.com/video/${encodeURIComponent(source.bvid)}`;
            link.target = '_blank';
            link.textContent = '评论原网址 ↗';
            link.style.cssText = 'color:#6796bd;text-decoration:none;';
            addRow('原网址', link);
        } else {
            addRow('原网址', '未知');
        }
        const updateDate = source.updateTime
            ? new Date(Number(source.updateTime) * 1000).toLocaleDateString('zh-CN')
            : '未知';
        addRow('最后更新', updateDate);
        addRow('数据数量', `${Number(source.commentCount) || 0} 条评论 · ${Number(source.replyCount) || 0} 条回复`);
        addRow('数据库', source.databasePath || '未知', source.databasePath || '');
        popover.appendChild(grid);
    }

    updateDisplayedCommentSourceName(source) {
        if (!source) return;
        if (this.commentCurrentSource === source && this.commentSourceButtonLabel) {
            const name = source.sourceName || source.bvid || '未命名来源';
            this.commentSourceButtonLabel.textContent = name;
            this.commentSourceButtonLabel.title = name;
        }
        this.renderCommentSourceMenu();
    }

    handleCommentSourceInfoSet(data) {
        const pending = this.commentSourceInfoPending;
        if (!pending || data.requestId !== pending.requestId
            || data.requestId !== this.commentSourceInfoRequestId) return;
        if (data.key === 'src-name') {
            pending.source.sourceName = String(data.value || pending.source.sourceName);
            this.updateDisplayedCommentSourceName(pending.source);
        }
        if (pending.editButton) pending.editButton.disabled = false;
        this.commentSourceInfoPending = null;
        this.commentSourceInfoRequestId = '';
    }

    refreshCommentHtml(resetPage = true) {
        if (resetPage) this.commentCurrentPage = 1;
        this.requestCommentHtml();
    }

    requestCommentHtml(updateReadRecord = false, updatePageSizeDefault = false) {
        const source = this.commentCurrentSource;
        if (!this.commentExpanded || !source || !this.currentEpisode) return;
        const requestId = `${this.widgetId}_comment_html_${++this.commentRequestSerial}`;
        //[DEBUG-START] 性能调试代码，release时删掉
        const perfStart = CS_COMMENT_PERF_DEBUG ? performance.now() : 0;
        this.commentPerformanceRequest = CS_COMMENT_PERF_DEBUG
            ? { requestId, started: perfStart, sent: 0 } : null;
        //[DEBUG-END]
        this.commentHtmlRequestId = requestId;
        this.setCommentContent('', '正在加载评论…');
        const keyword = this.commentKeywordInput ? this.commentKeywordInput.value.trim() : '';
        //[DEBUG-START] 性能调试代码，release时删掉
        if (this.commentPerformanceRequest) {
            this.commentPerformanceRequest.sent = performance.now();
            console.log(`[评论性能][${requestId}] 请求准备: ${(performance.now() - perfStart).toFixed(2)} ms`,
                { database: source.databasePath, page: this.commentCurrentPage,
                    pageSize: this.commentSettings.pageSize });
        }
        //[DEBUG-END]
        this.sendCommand('CS_GET_COMMENT_HTML', {
            requestId,
            metadataPath: this.currentCommentMetadataPath(),
            databasePath: source.databasePath,
            updateDir: source.updateDir || '',
            resourcePath: this.commentResourcePath(source),
            basicResourceFolder: source.basicResourceFolder || 'bilibili-resource',
            bvid: source.bvid || '',
            sortBy: this.commentSettings.sortBy,
            keywordEnabled: Boolean(keyword),
            keyword,
            page: this.commentCurrentPage,
            pageSize: this.commentSettings.pageSize,
            markDeleted: this.commentSettings.markDeleted,
            onlyDeleted: this.commentSettings.onlyDeleted,
            onlyVip: this.commentSettings.onlyVip,
            wordFilterEnabled: this.commentSettings.wordFilterEnabled,
            wordCount: this.commentSettings.wordCount,
            wordDirection: this.commentSettings.wordDirection,
            updateReadRecord,
            updatePageSizeDefault
        });
    }

    handleCommentHtml(data) {
        if (!this.commentExpanded || data.requestId !== this.commentHtmlRequestId) return;
        if (!this.commentCurrentSource
            || data.databasePath !== this.commentCurrentSource.databasePath) return;
        //[DEBUG-START] 性能调试代码，release时删掉
        const trace = this.commentPerformanceRequest;
        const perfEnabled = CS_COMMENT_PERF_DEBUG && trace && trace.requestId === data.requestId;
        let previous = performance.now();
        const records = [];
        const perfStep = perfEnabled ? (label) => {
            const now = performance.now();
            records.push({ stage: label, ms: +(now - previous).toFixed(2),
                totalMs: +(now - trace.started).toFixed(2) });
            previous = now;
        } : null;
        if (perfEnabled) {
            console.log(`[评论性能][${data.requestId}] 响应到达: ${(previous - trace.sent).toFixed(2)} ms（含后端、传输、消息排队及 JSON 解析）`,
                { htmlChars: (data.html || '').length });
        }
        //[DEBUG-END]
        this.commentCurrentPage = Math.max(1, Number(data.page) || 1);
        this.commentFilteredCount = Math.max(0, Number(data.totalCount) || 0);
        this.commentTotalPages = Math.max(1, Number(data.totalPages) || 1);
        this.setCommentContent(
            data.html || '',
            this.commentFilteredCount ? '评论加载失败' : '该来源没有评论'
        );
        this.renderCommentPagination();
        //[DEBUG-START] 性能调试代码，release时删掉
        if (perfStep) {
            perfStep('分页控件更新');
            console.log(`[评论性能][${data.requestId}] DOM 阶段`, records);
            requestAnimationFrame(() => requestAnimationFrame(() => {
                if (this.commentHtmlRequestId !== data.requestId || !this.commentExpanded) return;
                console.log(`[评论性能][${data.requestId}] 第二动画帧: ${(performance.now() - trace.started).toFixed(2)} ms（近似绘制时点，不代表图片已加载）`);
            }));
        }
        //[DEBUG-END]
    }

    handleCommentError(data) {
        let current = false;
        if (data.stage === 'info') {
            current = data.requestId === this.commentInfoRequestId;
        } else if (data.stage === 'source-info') {
            current = data.requestId === this.commentSourceInfoRequestId;
        } else {
            current = data.requestId === this.commentHtmlRequestId;
        }
        if (!current) return;
        console.error('[评论面板]', data.error || '评论数据加载失败');
        if (data.stage === 'source-info') {
            const pending = this.commentSourceInfoPending;
            if (pending && pending.requestId === data.requestId) {
                pending.source.sourceName = pending.previousName;
                if (pending.editButton) pending.editButton.disabled = false;
                this.updateDisplayedCommentSourceName(pending.source);
                if (this.commentSourceInfoPopover
                    && getComputedStyle(this.commentSourceInfoPopover).display !== 'none') {
                    this.renderCommentSourceInfo();
                }
            }
            this.commentSourceInfoPending = null;
            this.commentSourceInfoRequestId = '';
            return;
        }
        this.setCommentContent('', data.error || '评论数据加载失败');
    }

    setCommentPage(page) {
        const nextPage = Math.min(
            this.commentTotalPages,
            Math.max(1, Number(page) || 1)
        );
        if (nextPage === this.commentCurrentPage) return;
        this.commentCurrentPage = nextPage;
        this.renderCommentPagination();
        this.requestCommentHtml(true);
    }

    renderCommentPagination() {
        if (!this.commentPagination) return;
        const total = Math.max(1, Number(this.commentTotalPages) || 1);
        const current = Math.min(total, Math.max(1, Number(this.commentCurrentPage) || 1));
        this.commentPagination.innerHTML = '';
        const makeButton = (text, page, active = false, disabled = false) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = text;
            button.disabled = disabled;
            button.style.cssText = `height:30px;min-width:30px;padding:0 4px;border:${active ? '0' : '1px solid #eedde5'};border-radius:7px;background:${active ? '#e7a2bb' : '#fff'};color:${active ? '#fff' : '#817982'};font-size:15px;cursor:${disabled ? 'default' : 'pointer'};opacity:${disabled ? '.45' : '1'};`;
            if (!disabled && page) {
                button.addEventListener('click', () => this.setCommentPage(page));
            }
            return button;
        };
        if (current > 1) {
            this.commentPagination.appendChild(
                makeButton('上一页', current - 1)
            );
        }
        const visiblePages = new Set([1, total]);
        if (total <= 7) {
            for (let value = 1; value <= total; value += 1) {
                visiblePages.add(value);
            }
        } else if (current <= 4) {
            for (let value = 1; value <= Math.min(6, total); value += 1) {
                visiblePages.add(value);
            }
        } else if (current >= total - 3) {
            for (let value = Math.max(1, total - 5); value <= total; value += 1) {
                visiblePages.add(value);
            }
        } else {
            for (let value = current - 2; value <= current + 2; value += 1) {
                visiblePages.add(value);
            }
        }
        const sortedPages = [...visiblePages].sort((left, right) => left - right);
        const pages = [];
        sortedPages.forEach((value, index) => {
            if (index > 0 && value - sortedPages[index - 1] > 1) {
                pages.push('…');
            }
            pages.push(value);
        });
        pages.forEach((value) => {
            if (value === '…') {
                const ellipsis = document.createElement('span');
                ellipsis.textContent = '…';
                ellipsis.style.cssText = 'color:#aaa2aa;font-size:15px;';
                this.commentPagination.appendChild(ellipsis);
            } else {
                this.commentPagination.appendChild(
                    makeButton(String(value), value, value === current)
                );
            }
        });
        if (current < total) {
            this.commentPagination.appendChild(
                makeButton('下一页', current + 1)
            );
        }
    }

    /**
     * 展开或收起评论面板，并用 FLIP 动画连接按钮和面板的两个位置。
     * @param {Boolean} expanded - true 展开评论，false 收起评论。
     */
    setCommentExpanded(expanded) {
        if (!this.haveComment || !this.commentPanel || expanded === this.commentExpanded) return;

        const panel = this.commentPanel;
        const panelFirstRect = panel.getBoundingClientRect();
        const playerFirstRect = this.playerContainer.getBoundingClientRect();
        const layoutFirstRect = this.playerLayout.getBoundingClientRect();
        if (this.commentAnimation) {
            this.commentAnimation.cancel();
            this.commentAnimation = null;
        }
        if (this.playerCommentAnimation) {
            this.playerCommentAnimation.cancel();
            this.playerCommentAnimation = null;
        }
        this.commentExpanded = expanded;
        if (expanded) {
            this.commentContent.style.display = 'flex';
            this.commentContent.style.opacity = '0';
            this.commentContent.style.pointerEvents = 'none';
        } else {
            this.closeCommentPopovers();
            this.commentContent.style.opacity = '0';
            this.commentContent.style.pointerEvents = 'none';
            // 收起动画只需要面板外框参与 FLIP。立即移除不可见内容，避免它作为
            // 第二个 flex 子项挤偏重新出现的球形评论图标。
            this.commentContent.style.display = 'none';
            this.commentInfoRequestId = '';
            this.commentHtmlRequestId = '';
        }

        // 展开期间固定为展开前播放器占据的最大高度。播放器随后只在这个固定画布
        // 内移动和缩放，既不会带动下方内容跳动，评论面板也不会跟着播放器变矮。
        if (!this.commentExpandedLayoutHeight) {
            this.commentExpandedLayoutHeight = layoutFirstRect.height;
        }
        const lockedLayoutHeight = this.commentExpandedLayoutHeight;
        this.playerLayout.style.height = `${lockedLayoutHeight}px`;
        this.playerLayout.style.minHeight = `${lockedLayoutHeight}px`;
        this.playerLayout.style.maxHeight = `${lockedLayoutHeight}px`;

        if (expanded) {
            this.playerContainer.style.width = 'calc(60% - 39.6px)';
            this.playerContainer.style.maxWidth = 'none';
            this.playerContainer.style.margin = '0';
            this.playerContainer.style.alignSelf = 'center';
            this.playerLayout.style.gap = '16px';
            this.playerLayout.appendChild(panel);
            panel.title = '';
            panel.setAttribute('aria-label', '评论面板');
            Object.assign(panel.style, {
                position: 'relative',
                top: 'auto',
                right: 'auto',
                width: 'calc(40% - 16.4px)',
                height: '100%',
                maxHeight: '100%',
                minWidth: '0',
                flex: '0 0 calc(40% - 16.4px)',
                alignSelf: 'stretch',
                borderRadius: '12px',
                background: '#fff',
                color: '#4A90D9',
                cursor: 'default',
                transform: 'none',
                zIndex: 'auto'
            });
            this.commentIcon.style.display = 'none';
            this.commentCollapseButton.style.display = 'block';
            this.requestCommentInfo();
        } else {
            this.playerContainer.style.width = '80%';
            this.playerContainer.style.maxWidth = '1000px';
            this.playerContainer.style.margin = '0 auto';
            this.playerContainer.style.alignSelf = 'flex-start';
            this.playerLayout.style.gap = '0';
            this.commentBackButtonBar.appendChild(panel);
            panel.title = '显示评论';
            panel.setAttribute('aria-label', '显示评论');
            Object.assign(panel.style, {
                position: 'absolute',
                top: '8px',
                right: 'calc(100% + 10px)',
                width: '40px',
                height: '40px',
                maxHeight: 'none',
                minWidth: '40px',
                flex: 'none',
                alignSelf: 'auto',
                borderRadius: '50%',
                background: '#4A90D9',
                color: '#fff',
                cursor: 'pointer',
                transform: 'none',
                zIndex: '101'
            });
            this.commentIcon.style.display = 'block';
            this.commentCollapseButton.style.display = 'none';
        }

        const panelLastRect = panel.getBoundingClientRect();
        const playerLastRect = this.playerContainer.getBoundingClientRect();
        const canAnimatePanel = panel.animate
            && panelFirstRect.width > 0 && panelLastRect.width > 0
            && panelFirstRect.height > 0 && panelLastRect.height > 0;
        const canAnimatePlayer = this.playerContainer.animate
            && playerFirstRect.width > 0 && playerLastRect.width > 0
            && playerFirstRect.height > 0 && playerLastRect.height > 0;

        if (canAnimatePanel) {
            const panelDeltaX = panelFirstRect.left - panelLastRect.left;
            const panelDeltaY = panelFirstRect.top - panelLastRect.top;
            const panelScaleX = panelFirstRect.width / panelLastRect.width;
            const panelScaleY = panelFirstRect.height / panelLastRect.height;
            const panelAnimation = panel.animate([
                {
                    transformOrigin: 'top left',
                    transform: `translate(${panelDeltaX}px, ${panelDeltaY}px) scale(${panelScaleX}, ${panelScaleY})`,
                    borderRadius: expanded ? '50%' : '12px',
                    background: expanded ? '#4A90D9' : '#fff'
                },
                {
                    transformOrigin: 'top left',
                    transform: 'translate(0, 0) scale(1, 1)',
                    borderRadius: expanded ? '12px' : '50%',
                    background: expanded ? '#fff' : '#4A90D9'
                }
            ], {
                duration: 420,
                easing: 'cubic-bezier(0.22, 1, 0.36, 1)'
            });
            this.commentAnimation = panelAnimation;
            panelAnimation.onfinish = () => {
                if (this.commentAnimation === panelAnimation) {
                    this.commentAnimation = null;
                }
                if (expanded && this.commentExpanded) {
                    this.commentContent.style.opacity = '1';
                    this.commentContent.style.pointerEvents = 'auto';
                } else if (!expanded && !this.commentExpanded) {
                    this.commentContent.style.display = 'none';
                }
            };
            panelAnimation.oncancel = panelAnimation.onfinish;
        } else if (expanded && this.commentExpanded) {
            this.commentContent.style.opacity = '1';
            this.commentContent.style.pointerEvents = 'auto';
        } else if (!expanded && !this.commentExpanded) {
            this.commentContent.style.display = 'none';
        }

        const finishPlayerTransition = () => {
            if (!expanded && !this.commentExpanded) {
                this.playerLayout.style.height = '';
                this.playerLayout.style.minHeight = '';
                this.playerLayout.style.maxHeight = '';
                this.commentExpandedLayoutHeight = 0;
            }
        };

        if (!canAnimatePlayer) {
            if (expanded && this.commentExpanded) {
                this.commentContent.style.opacity = '1';
                this.commentContent.style.pointerEvents = 'auto';
            } else if (!expanded && !this.commentExpanded) {
                this.commentContent.style.display = 'none';
            }
            finishPlayerTransition();
            return;
        }

        const playerDeltaX = playerFirstRect.left - playerLastRect.left;
        const playerScaleX = playerFirstRect.width / playerLastRect.width;
        const playerScaleY = playerFirstRect.height / playerLastRect.height;
        // 最终布局已把播放器垂直居中；以左边中点缩放可让整个动画期间的
        // 垂直中心保持不变，同时让播放器抵达左边界后再向右侧收缩。
        const playerKeyframes = expanded ? [
            {
                offset: 0,
                transformOrigin: 'left center',
                transform: `translate(${playerDeltaX}px, 0) scale(${playerScaleX}, ${playerScaleY})`
            },
            {
                offset: 0.55,
                transformOrigin: 'left center',
                transform: `translate(0, 0) scale(${playerScaleX}, ${playerScaleY})`
            },
            {
                offset: 1,
                transformOrigin: 'left center',
                transform: 'translate(0, 0) scale(1, 1)'
            }
        ] : [
            {
                offset: 0,
                transformOrigin: 'left center',
                transform: `translate(${playerDeltaX}px, 0) scale(${playerScaleX}, ${playerScaleY})`
            },
            {
                offset: 0.45,
                transformOrigin: 'left center',
                transform: `translate(${playerDeltaX}px, 0) scale(1, 1)`
            },
            {
                offset: 1,
                transformOrigin: 'left center',
                transform: 'translate(0, 0) scale(1, 1)'
            }
        ];
        const playerAnimation = this.playerContainer.animate(playerKeyframes, {
            duration: 420,
            easing: 'cubic-bezier(0.22, 1, 0.36, 1)'
        });
        this.playerCommentAnimation = playerAnimation;
        playerAnimation.onfinish = () => {
            if (this.playerCommentAnimation === playerAnimation) {
                this.playerCommentAnimation = null;
                finishPlayerTransition();
            }
        };
        playerAnimation.oncancel = () => {
            if (this.playerCommentAnimation === playerAnimation) {
                this.playerCommentAnimation = null;
            }
        };
    }

    /** 清理评论面板仍在执行的动画和 DOM 引用。 */
    disposeCommentPanel() {
        clearTimeout(this.commentKeywordTimer);
        this.commentKeywordTimer = null;
        if (this.commentOutsideClickHandler) {
            document.removeEventListener('pointerdown', this.commentOutsideClickHandler, true);
            this.commentOutsideClickHandler = null;
        }
        if (this.commentAnimation) {
            this.commentAnimation.cancel();
            this.commentAnimation = null;
        }
        if (this.playerCommentAnimation) {
            this.playerCommentAnimation.cancel();
            this.playerCommentAnimation = null;
        }
        if (this.commentScrollbarCleanup) {
            this.commentScrollbarCleanup();
            this.commentScrollbarCleanup = null;
        }
        if (this.commentFontStyleElement) {
            this.commentFontStyleElement.remove();
            this.commentFontStyleElement = null;
        }
        if (this.playerLayout) {
            this.playerLayout.style.height = '';
            this.playerLayout.style.minHeight = '';
            this.playerLayout.style.maxHeight = '';
        }
        if (this.commentPanel) {
            this.commentPanel.remove();
        }
        if (this.commentImagePreviewModal) {
            this.commentImagePreviewModal.remove();
        }
        this.commentPanel = null;
        this.commentImagePreviewModal = null;
        this.commentIcon = null;
        this.commentCollapseButton = null;
        this.commentBackButtonBar = null;
        this.commentContent = null;
        this.commentScrollContainer = null;
        this.commentRoot = null;
        this.commentList = null;
        this.commentTemplate = CS_COMMENT_DIV_TEMPLATE;
        this.commentSourceMenu = null;
        this.commentSourceInfoPopover = null;
        this.commentOptionsPopover = null;
        this.commentSettingsPopover = null;
        this.commentPagination = null;
        this.commentPageSizeInput = null;
        this.commentPageSizeMenu = null;
        this.commentInfoRequestId = '';
        this.commentHtmlRequestId = '';
        this.commentSourceInfoRequestId = '';
        this.commentSourceInfoPending = null;
        this.commentExpanded = false;
        this.commentExpandedLayoutHeight = 0;
    }

    createBackButtons(container) {
        const menuBar = document.createElement('div');
        menuBar.style.position = 'absolute';
        menuBar.style.top = '10px';
        menuBar.style.right = '20px';
        menuBar.style.display = 'flex';
        menuBar.style.gap = '10px';
        menuBar.style.zIndex = '100';
        menuBar.style.padding = '8px 12px';
        menuBar.style.background = 'rgba(200, 220, 255, 0.9)';
        menuBar.style.borderRadius = '20px';
        menuBar.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';

        const backBtn = document.createElement('button');
        backBtn.style.cssText = 'width:40px;height:40px;border:none;border-radius:50%;background:#4A90D9;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;';
        backBtn.innerHTML = `<svg viewBox="-1.5 0 19 19" width="30" height="30" fill="white"><path d="M15.036 9.577a1.03 1.03 0 0 1-1.03 1.03H4.479l2.76 2.759a1.03 1.03 0 0 1-1.456 1.455l-4.516-4.516a1.029 1.029 0 0 1 0-1.455l4.516-4.516a1.03 1.03 0 1 1 1.455 1.455l-2.76 2.76h9.53a1.03 1.03 0 0 1 1.029 1.028z"/></svg>`;
        backBtn.onmouseover = () => { backBtn.style.background = '#357ABD'; backBtn.style.transform = 'scale(1.05)'; };
        backBtn.onmouseout = () => { backBtn.style.background = '#4A90D9'; backBtn.style.transform = 'scale(1)'; };
        backBtn.onclick = () => pop_page(1);

        const rootBtn = document.createElement('button');
        rootBtn.style.cssText = 'width:40px;height:40px;border:none;border-radius:50%;background:#4A90D9;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;';
        rootBtn.innerHTML = `<svg viewBox="-1.5 0 19 19" width="30" height="30" fill="white"><path d="M14.993 7.61a.554.554 0 0 1-.756.207L7.98 4.255 1.764 7.817a.554.554 0 0 1-.55-.962l1.192-.683v-2.48a.476.476 0 0 1 .475-.474h1.222a.476.476 0 0 1 .475.475v1.234l3.126-1.79a.554.554 0 0 1 .55-.001l6.531 3.718a.554.554 0 0 1 .208.756zm-1.399.937v6.198a.476.476 0 0 1-.475.475H2.881a.476.476 0 0 1-.475-.475v-6.2L7.98 5.353zm-6.782 1.01H4.578v2.262h2.234zm4.61 0H9.188v2.262h2.234z"/></svg>`;
        rootBtn.onmouseover = () => { rootBtn.style.background = '#357ABD'; rootBtn.style.transform = 'scale(1.05)'; };
        rootBtn.onmouseout = () => { rootBtn.style.background = '#4A90D9'; rootBtn.style.transform = 'scale(1)'; };
        rootBtn.onclick = () => pop_page(256);

        menuBar.appendChild(backBtn);
        menuBar.appendChild(rootBtn);
        container.appendChild(menuBar);
    }

    renderEpisodeBar() {
        if (!this.haveEpisodeBar || !this.episodeScrollContainer) return;
        this.episodeScrollContainer.innerHTML = '';
        
        this.episodes.forEach(ep => {
            const isCurrent = this.currentEpisode && ep.order === this.currentEpisode.order;
            const epBtn = document.createElement('button');
            epBtn.style.cssText = `
                display:inline-flex;flex-direction:column;align-items:center;justify-content:center;
                width:100px;padding:10px 8px;margin:5px;border-radius:8px;cursor:pointer;transition:all 0.3s;
                background:${isCurrent ? '#4A90D9' : 'rgba(255,255,255,0.1)'};
                border:2px solid ${isCurrent ? '#6ab0ff' : 'transparent'};
                color:${isCurrent ? '#fff' : '#aaa'};
                font-size:12px;
            `;
            if (isCurrent) {
                epBtn.classList.add('cs-current-episode');
            }
            
            epBtn.onmouseover = () => {
                if (!isCurrent) {
                    epBtn.style.background = 'rgba(255,255,255,0.2)';
                    epBtn.style.color = '#fff';
                }
            };
            
            epBtn.onmouseout = () => {
                if (!isCurrent) {
                    epBtn.style.background = 'rgba(255,255,255,0.1)';
                    epBtn.style.color = '#aaa';
                }
            };

            const orderDiv = document.createElement('div');
            orderDiv.style.cssText = `font-size:14px;font-weight:bold;margin-bottom:2px;${isCurrent ? 'color:#fff' : 'color:#ccc'};`;
            orderDiv.textContent = `第${ep.order}集`;
            epBtn.appendChild(orderDiv);

            if (ep.name) {
                const nameDiv = document.createElement('div');
                nameDiv.style.cssText = 'font-size:10px;white-space:normal;text-align:center;line-height:1.2;';
                nameDiv.textContent = ep.name;
                epBtn.appendChild(nameDiv);
            }

            if (ep.hasDanmu) {
                const danmuBadge = document.createElement('div');
                danmuBadge.style.cssText = 'margin-top:4px;padding:2px 6px;background:#FF69B4;color:#fff;border-radius:8px;font-size:9px;';
                danmuBadge.textContent = '弹幕';
                epBtn.appendChild(danmuBadge);
            }

            // 点击切换剧集
            epBtn.onclick = () => {
                // 保存当前时间
                this.saveCurrentTime();
                this.currentEpisode = ep;
                this.renderEpisodeBar();
                this.scrollToCurrentEpisode();
                this.switchEpisode(ep);
            };

            this.episodeScrollContainer.appendChild(epBtn);
        });
    }

    scrollToCurrentEpisode() {
        if (!this.currentEpisode || !this.episodeScrollContainer) return;
        
        const currentBtn = this.episodeScrollContainer.querySelector('.cs-current-episode');
        if (currentBtn) {
            currentBtn.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center'
            });
        }
    }

    initPlayer(playerId) {
        if (!this.currentEpisode) return;

        const nativePlayback = this.isNativeVideo(this.currentEpisode.path);
        const videoPath = nativePlayback ? this.getVideoUrl(this.currentEpisode.path) : '';
        const hasDanmu = this.currentEpisode.hasDanmu;

        // 如果有弹幕，加载弹幕脚本
        // if (hasDanmu) {
        //     this.loadDanmuScript(this.currentEpisode.path);
        // }

        // 创建播放器
        const container = document.getElementById(playerId);
        if (!container) return;
        // 清空容器内容
        container.innerHTML = '';

        const playerOptions = {
            container: `#${playerId}`,
            autoplay: false,
            poster: '',
            autoSeekTime: nativePlayback ? (this.autoSeekTime || 0) : 0,
            controls: [
                ['play', 'volume', 'time', 'spacer', 'airplay', 'settings', 'web-fullscreen', 'fullscreen'],
                ['progress'],
                [{
                    name: 'danmaku-send',
                    position: 'right'
                }, {
                    name: 'danmaku-settings',
                    position: 'right'
                }]
            ]
        };
        if (nativePlayback) {
            playerOptions.src = videoPath;
        }

        // 添加弹幕插件（弹幕数据已包含配置）
        if (hasDanmu && window.NPlayerDanmaku && this.danmakuData) {
            playerOptions.plugins = [new NPlayerDanmaku(this.danmakuData)];
        }

        // 创建播放器实例
        this.player = new NPlayer.Player(playerOptions);
        this.player.mount();

        if (!nativePlayback) {
            this.setupRemuxStream(this.autoSeekTime || 0);
        }

        // 使用防抖函数，避免频繁保存
        let saveTimer = null;
        
        // 监听弹幕配置变更事件
        let oop = this.player.on("DanmakuUpdateOptions", () => {
            const opts = this.player.danmaku.opts;
            const configToSave = {
                speed: opts.speed,
                fontsizeScale: opts.fontsizeScale,
                area: opts.area
            };
            console.log('弹幕配置变更:', configToSave);
            // 防抖保存
            if (saveTimer) {
                clearTimeout(saveTimer);
            }
            saveTimer = setTimeout(() => {
                this.saveDanmakuConfig(configToSave);
            }, 500);
        });

        this.player.on("AfterInit", () => {
            console.log('播放器就绪');
            if (hasDanmu && this.player.danmaku) {
                console.log('弹幕数量:', this.player.danmaku.getItems().length);
            }
        });
        //console.log('播放器初始化完成',this.player.EVENT.AFTER_INIT);

    }

    switchEpisode(episode) {
        this.disposeRemuxStream();
        this.danmakuData = null;
        this.autoSeekTime = 0;
        if (this.player && this.player.dispose) {
            this.player.dispose();
        }
        this.player = null;
        if (this.haveComment && this.commentExpanded) {
            this.resetCommentPanelForEpisode(true);
        }
        this.sendCommand('GET_CS_VIDEO_DATA', {
            rootPath: this.rootPath,
            videoPath: episode.path
        });
    }

    isNativeVideo(path) {
        const extension = String(path || '').split('.').pop().toLowerCase();
        return ['mp4', 'm4v', 'webm', 'ogv', 'ogg'].includes(extension);
    }

    setupRemuxStream(startTime) {
        if (!window.MediaSource) {
            this.showStreamError('当前浏览器不支持 MediaSource，无法播放该视频格式');
            return;
        }
        const video = this.player && this.player.video;
        if (!video) return;

        this.streamSeekingHandler = () => {
            if (this.restartingStream || this.streamFailed
                || this.isTimeBuffered(video.currentTime)) return;
            const seekTime = Math.max(0, Number(video.currentTime) || 0);
            clearTimeout(this.streamSeekTimer);
            this.streamSeekTimer = setTimeout(() => {
                this.openRemuxMediaSource(seekTime, 'SEEK_VIDEO_STREAM');
            }, 180);
        };
        this.streamPlayHandler = () => {
            if (!this.restartingStream || this.streamFailed) return;
            const target = this.getStreamPrebufferTarget();
            const bufferedAhead = this.getBufferedAhead(this.streamStartTime);
            if (bufferedAhead + 0.05 >= target) return;

            // 记录用户的播放意图，但在达到预缓冲阈值前不让播放头消耗数据。
            this.resumeAfterStreamOpen = true;
            video.pause();
            if (!this.streamPrebufferNoticeShown) {
                this.streamPrebufferNoticeShown = true;
                if (this.player && this.player.toast) {
                    this.player.toast.show(`正在预缓冲，达到 ${target.toFixed(0)} 秒后开始播放`, 'center', 3);
                }
            }
        };
        this.streamTimeUpdateHandler = () => this.requestMoreStreamData();
        this.streamWaitingHandler = () => this.requestMoreStreamData(true);
        video.addEventListener('seeking', this.streamSeekingHandler);
        video.addEventListener('play', this.streamPlayHandler);
        video.addEventListener('timeupdate', this.streamTimeUpdateHandler);
        video.addEventListener('waiting', this.streamWaitingHandler);
        this.openRemuxMediaSource(startTime, 'START_VIDEO_STREAM');
    }

    openRemuxMediaSource(startTime, command) {
        const video = this.player && this.player.video;
        if (!video || !this.currentEpisode) return;

        this.clearUnsupportedVideoNotice();
        this.resumeAfterStreamOpen = !video.paused;
        this.restartingStream = true;
        this.streamStartTime = Math.max(0, Number(startTime) || 0);
        this.activeStreamId = null;
        this.streamQueue = [];
        this.currentStreamSegment = null;
        this.streamEnded = false;
        this.streamFailed = false;
        this.streamRequestedUntil = 0;
        this.streamLastTrimBefore = 0;
        this.streamPrebufferNoticeShown = false;
        this.releaseMediaSource();

        this.mediaSource = new MediaSource();
        this.streamObjectUrl = URL.createObjectURL(this.mediaSource);
        video.src = this.streamObjectUrl;
        this.mediaSource.addEventListener('sourceopen', () => {
            this.sendCommand(command, {
                rootPath: this.rootPath,
                videoPath: this.currentEpisode.path,
                startTime: this.streamStartTime
            });
        }, { once: true });
    }

    handleVideoStreamReady(data) {
        if (!this.mediaSource || this.mediaSource.readyState !== 'open') return;
        if (!MediaSource.isTypeSupported(data.mimeType)) {
            this.failRemuxStream(`浏览器不支持该视频编码组合：${data.mimeType}`);
            return;
        }

        this.activeStreamId = data.streamId;
        this.streamStartTime = Number(data.startTime) || 0;
        this.streamDuration = Number(data.duration) || 0;
        const serverHighWater = Number(data.bufferHighWaterSeconds) || 0;
        if (serverHighWater > this.streamBufferLowWaterSeconds) {
            this.streamBufferHighWaterSeconds = serverHighWater;
        }
        this.streamRequestedUntil = this.streamStartTime + this.streamBufferHighWaterSeconds;
        if (this.streamDuration > 0) {
            this.streamRequestedUntil = Math.min(this.streamRequestedUntil, this.streamDuration);
        }
        const requestedStartTime = Number(data.requestedStartTime) || 0;
        console.log('[视频流] 准备播放', {
            mimeType: data.mimeType,
            requestedStartTime: requestedStartTime,
            startTime: this.streamStartTime,
            duration: this.streamDuration,
            prebufferSeconds: this.getStreamPrebufferTarget(),
            lowWaterSeconds: this.streamBufferLowWaterSeconds,
            highWaterSeconds: this.streamBufferHighWaterSeconds
        });
        if (Math.abs(this.streamStartTime - requestedStartTime) > 0.05) {
            console.log(
                `[视频流] Seek 已对齐关键帧：${requestedStartTime.toFixed(3)}s -> `
                + `${this.streamStartTime.toFixed(3)}s`
            );
        }
        try {
            this.sourceBuffer = this.mediaSource.addSourceBuffer(data.mimeType);
            this.sourceBuffer.mode = 'segments';
            this.sourceBuffer.timestampOffset = this.streamStartTime;
            this.sourceBuffer.addEventListener('updateend', () => {
                this.setInitialStreamPositionIfReady();
                if (this.trimOldStreamBuffer()) {
                    this.requestMoreStreamData();
                    return;
                }
                this.appendNextStreamChunk();
                this.requestMoreStreamData();
                this.finishMediaStreamIfPossible();
            });
            this.sourceBuffer.addEventListener('error', () => {
                const segment = this.currentStreamSegment;
                const detail = segment
                    ? `（${segment.segmentType} 分段 #${segment.sequence}，${segment.payload.byteLength} 字节）`
                    : '';
                this.failRemuxStream(`浏览器解析 FFmpeg 视频流失败${detail}`);
            });
            if (this.streamDuration > 0) {
                this.mediaSource.duration = this.streamDuration;
            }
            this.appendNextStreamChunk();
        } catch (error) {
            this.failRemuxStream(`无法创建视频缓冲区：${error.message}`);
        }
    }

    handleUnsupportedVideoStream(data) {
        const message = data.message || '不支持该视频的视频编码格式';
        this.streamFailed = true;
        this.streamQueue = [];
        this.currentStreamSegment = null;
        this.activeStreamId = null;
        this.sendCommand('CANCEL_VIDEO_STREAM');
        this.releaseMediaSource();

        const video = this.player && this.player.video;
        if (video) {
            video.pause();
            video.removeAttribute('src');
            video.load();
        }
        this.showStreamError(message);

        this.clearUnsupportedVideoNotice();
        const playerContainer = document.getElementById(this.playerContainerId);
        if (!playerContainer) return;
        const notice = document.createElement('div');
        notice.style.cssText = `
            position:absolute;inset:0;z-index:1000;display:flex;flex-direction:column;
            align-items:center;justify-content:center;gap:10px;text-align:center;
            color:#fff;background:rgba(18,18,28,0.94);font-size:20px;font-weight:600;
        `;
        const title = document.createElement('div');
        title.textContent = message;
        notice.appendChild(title);
        if (data.videoCodec) {
            const detail = document.createElement('div');
            detail.style.cssText = 'color:#aaa;font-size:13px;font-weight:400;';
            detail.textContent = `检测到的视频编码：${data.videoCodec}`;
            notice.appendChild(detail);
        }
        playerContainer.appendChild(notice);
        this.streamUnsupportedNotice = notice;
    }

    clearUnsupportedVideoNotice() {
        if (this.streamUnsupportedNotice && this.streamUnsupportedNotice.parentNode) {
            this.streamUnsupportedNotice.parentNode.removeChild(this.streamUnsupportedNotice);
        }
        this.streamUnsupportedNotice = null;
    }

    appendNextStreamChunk() {
        if (!this.sourceBuffer || this.sourceBuffer.updating || this.streamQueue.length === 0) return;
        try {
            this.currentStreamSegment = this.streamQueue.shift();
            this.sourceBuffer.appendBuffer(this.currentStreamSegment.payload);
        } catch (error) {
            this.failRemuxStream(`写入视频缓冲区失败：${error.message}`);
        }
    }

    setInitialStreamPositionIfReady() {
        const video = this.player && this.player.video;
        if (!video || !this.sourceBuffer || !this.restartingStream) return;
        const bufferedAhead = this.getBufferedAhead(this.streamStartTime);
        if (bufferedAhead <= 0) return;

        const prebufferTarget = this.getStreamPrebufferTarget();
        if (!this.streamEnded && bufferedAhead + 0.05 < prebufferTarget) {
            if (!video.paused) {
                this.resumeAfterStreamOpen = true;
                video.pause();
            }
            return;
        }

        video.currentTime = this.streamStartTime;
        this.restartingStream = false;
        this.streamPrebufferNoticeShown = false;
        console.log('[视频流] 预缓冲完成', {
            bufferedAhead: bufferedAhead,
            target: prebufferTarget,
            startTime: this.streamStartTime
        });
        if (this.resumeAfterStreamOpen) {
            video.play().catch(error => console.warn('恢复播放失败:', error));
        }
    }

    getStreamPrebufferTarget() {
        if (this.streamDuration <= 0) return this.streamPrebufferSeconds;
        const remaining = Math.max(0.1, this.streamDuration - this.streamStartTime);
        return Math.min(this.streamPrebufferSeconds, remaining);
    }

    getBufferedAhead(time) {
        const video = this.player && this.player.video;
        if (!video) return 0;
        for (let index = 0; index < video.buffered.length; index++) {
            if (time >= video.buffered.start(index) - 0.05
                && time <= video.buffered.end(index) + 0.05) {
                return Math.max(0, video.buffered.end(index) - time);
            }
        }
        return 0;
    }

    isTimeBuffered(time) {
        return this.getBufferedAhead(time) > 0;
    }

    requestMoreStreamData(force = false) {
        const video = this.player && this.player.video;
        if (!video || !this.activeStreamId || this.streamEnded || this.streamFailed) return;
        const playbackTime = this.restartingStream
            ? this.streamStartTime
            : Math.max(this.streamStartTime, Number(video.currentTime) || 0);
        const bufferedAhead = this.getBufferedAhead(playbackTime);
        if (!force && bufferedAhead > this.streamBufferLowWaterSeconds) return;

        let bufferUntil = playbackTime + this.streamBufferHighWaterSeconds;
        if (this.streamDuration > 0) {
            bufferUntil = Math.min(bufferUntil, this.streamDuration);
        }
        const needsFinalRequest = this.streamDuration > 0
            && bufferUntil >= this.streamDuration - 0.05
            && this.streamRequestedUntil < this.streamDuration - 0.05;
        if (!needsFinalRequest && bufferUntil <= this.streamRequestedUntil + 0.5) return;
        if (this.sendCommand('BUFFER_VIDEO_STREAM', {
            streamId: this.activeStreamId,
            bufferUntil: bufferUntil
        })) {
            this.streamRequestedUntil = bufferUntil;
            console.log('[视频流] 缓冲低于低水位，请求后续数据', {
                bufferedAhead: bufferedAhead,
                bufferUntil: bufferUntil
            });
        }
    }

    trimOldStreamBuffer() {
        const video = this.player && this.player.video;
        if (!video || this.restartingStream || this.streamQueue.length > 0
            || !this.sourceBuffer || this.sourceBuffer.updating) return false;
        const removeBefore = (Number(video.currentTime) || 0) - this.streamRetainBehindSeconds;
        if (removeBefore <= this.streamLastTrimBefore + 10) return false;

        let hasOldData = false;
        for (let index = 0; index < video.buffered.length; index++) {
            if (video.buffered.start(index) < removeBefore - 0.05) {
                hasOldData = true;
                break;
            }
        }
        if (!hasOldData) return false;
        try {
            this.sourceBuffer.remove(0, removeBefore);
            this.streamLastTrimBefore = removeBefore;
            return true;
        } catch (error) {
            console.warn('[视频流] 清理旧缓冲失败:', error);
            return false;
        }
    }

    finishMediaStreamIfPossible() {
        if (!this.streamEnded || this.streamQueue.length > 0
            || !this.sourceBuffer || this.sourceBuffer.updating
            || !this.mediaSource || this.mediaSource.readyState !== 'open') return;
        try {
            this.mediaSource.endOfStream();
        } catch (error) {
            console.warn('结束 MediaSource 失败:', error);
        }
    }

    releaseMediaSource() {
        if (this.sourceBuffer && this.sourceBuffer.updating) {
            try { this.sourceBuffer.abort(); } catch (error) { /* 已关闭时忽略 */ }
        }
        this.sourceBuffer = null;
        if (this.mediaSource && this.mediaSource.readyState === 'open') {
            try { this.mediaSource.endOfStream(); } catch (error) { /* 已结束时忽略 */ }
        }
        this.mediaSource = null;
        if (this.streamObjectUrl) {
            URL.revokeObjectURL(this.streamObjectUrl);
            this.streamObjectUrl = null;
        }
    }

    disposeRemuxStream() {
        clearTimeout(this.streamSeekTimer);
        const video = this.player && this.player.video;
        if (video && this.streamSeekingHandler) {
            video.removeEventListener('seeking', this.streamSeekingHandler);
        }
        if (video && this.streamPlayHandler) {
            video.removeEventListener('play', this.streamPlayHandler);
        }
        if (video && this.streamTimeUpdateHandler) {
            video.removeEventListener('timeupdate', this.streamTimeUpdateHandler);
        }
        if (video && this.streamWaitingHandler) {
            video.removeEventListener('waiting', this.streamWaitingHandler);
        }
        this.streamSeekingHandler = null;
        this.streamPlayHandler = null;
        this.streamTimeUpdateHandler = null;
        this.streamWaitingHandler = null;
        if (this.activeStreamId || this.mediaSource) {
            this.sendCommand('CANCEL_VIDEO_STREAM');
        }
        this.releaseMediaSource();
        this.activeStreamId = null;
        this.streamQueue = [];
        this.currentStreamSegment = null;
        this.restartingStream = false;
        this.streamFailed = false;
        this.clearUnsupportedVideoNotice();
    }

    failRemuxStream(message) {
        if (this.streamFailed) return;
        this.streamFailed = true;
        this.streamQueue = [];
        this.sendCommand('CANCEL_VIDEO_STREAM');
        this.showStreamError(message);
        this.releaseMediaSource();
    }

    showStreamError(message) {
        console.error('[视频流]', message);
        this.restartingStream = false;
        if (this.player && this.player.toast) {
            this.player.toast.show(message, 'center', 6);
        }
    }
    

    sendCommand(command, data = {}) {
        if (socket && socket.isConnected()) {
            return socket.send(JSON.stringify({
                command: command,
                widgetId: this.widgetId,
                ...data
            }));
        }
        return false;
    }

    saveDanmakuConfig(config) {
        this.sendCommand('SET_DANMAKU_CONFIG', {
            widgetId: this.widgetId,
            danmakuConfig: config
        });
    }

    loadNPlayerScripts() {
        // 检查是否已加载NPlayer库
        if (window.NPlayer && window.NPlayerDanmaku) {
            return;
        }

        // 创建加载标记避免重复加载
        if (this.nplayerLoaded) {
            return;
        }
        this.nplayerLoaded = true;

        // 加载NPlayer核心库
        const nplayerScript = document.createElement('script');
        nplayerScript.src = '/frontend/player/nplayer.min.js';
        nplayerScript.onload = () => {
            console.log('NPlayer核心库加载完成');
        };
        nplayerScript.onerror = (err) => {
            console.error('NPlayer核心库加载失败:', err);
        };
        document.head.appendChild(nplayerScript);

        // 加载弹幕插件
        const danmakuScript = document.createElement('script');
        danmakuScript.src = '/frontend/player/index.min.js';
        danmakuScript.onload = () => {
            console.log('NPlayer弹幕插件加载完成');
        };
        danmakuScript.onerror = (err) => {
            console.error('NPlayer弹幕插件加载失败:', err);
        };
        document.head.appendChild(danmakuScript);
    }

    getVideoUrl(path) {
        // 构建视频文件的URL
        // 假设rootPath是服务器上的路径
        return `${this.rootPath}/${encodeURIComponent(path)}`;
    }

    saveCurrentTime() {
        if (this.player && this.currentEpisode) {
            const currentTime = this.player.currentTime || 0;
            this.sendCommand('SAVE_WATCH_RECORD', {
                rootPath: this.rootPath,
                videoPath: this.currentEpisode.path,
                videoTime: currentTime,
                episodeOrder: this.currentEpisode.order || 0
            });
        }
    }
}

/**
 * 番剧播放器页面组件。
 *
 * 通过组合通用视频播放器组件保留番剧页面的独立扩展入口，后续番剧专属功能
 * 可以放在本类中，而不必继续增加 CS_VideoPlayerWidget 的通用接口负担。
 */
class CS_AnimeVideoPlayerWidget {
    constructor(rootPath, episodes, currentEpisode) {
        // 番剧页面实际使用的通用视频播放器组件。
        this.videoPlayerWidget = new CS_VideoPlayerWidget(
            rootPath,
            episodes,
            currentEpisode,
            true,
            true
        );
    }

    render(container) {
        this.videoPlayerWidget.render(container);
        
    }
}

window.CS_VideoPlayerWidget = CS_VideoPlayerWidget;
window.CS_AnimeVideoPlayerWidget = CS_AnimeVideoPlayerWidget;

window.CS_AnimeWidget = CS_AnimeWidget;
