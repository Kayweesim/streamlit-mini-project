import './style.css'
import javascriptLogo from './assets/javascript.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import { setupCounter } from './counter.js'

document.querySelector('#app').innerHTML = `    
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Document</title>
        <link rel="stylesheet" href="./style.css" />
      </head>



    <body>
      <h1> Hello Test!</h1>

      <counter> 123 </counter>

      <h2> A heading of text </h2>
      

      <p> A paragraph of text </p>

      <span> A span of text </span>

      <strong> A strong of text </strong>
      
      <div> A div of text </div>




    </body>
    
`

setupCounter(document.querySelector('#counter'))
