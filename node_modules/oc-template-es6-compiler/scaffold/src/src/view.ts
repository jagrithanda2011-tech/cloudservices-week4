import { InitialData, serverClient, getSettings } from 'oc-server/client';
import styles from './styles.css';
import logo from '../public/logo.png';

const onRender = (cb: (element: HTMLElement) => void) => {
  const isBrowser = typeof window !== 'undefined';
  if (isBrowser) {
    const { id } = getSettings();
    window.oc.events.on('oc:rendered', (e, data) => {
      if (String(data.id) === id) {
        cb(data.element);
      }
    });
  }
};

export default ({ firstName, lastName, hobbies, born }: InitialData) => {
  onRender((element) => {
    element
      .querySelector(`.${styles.button}`)
      ?.addEventListener('click', async () => {
        const { funFact } = await serverClient.funFact({ year: born });
        element.querySelector('#fun-year-fact')!.innerHTML = funFact;
      });
  });

  return /* html */ `
    <div class="${styles.container}">
      <img width="50" height="50" src="${logo}" alt="Logo" />
      <h1 style="margin: 0 0 20px 0;">
        Hello, <span style="text-decoration: underline;">${firstName}</span> ${lastName}
      </h1>
      <div class=${styles.info}>
        <div class=${styles.block}>Born: ${born}</div>
        <div class=${styles.block}>
          <div>Hobbies: ${hobbies.map((x) => x.toLowerCase()).join(', ')}</div>
        </div>
      </div>
      <div id="fun-year-fact"></div>
      <button class=${styles.button}>
        Fun year fact
      </button>
    </div>
  `;
};
