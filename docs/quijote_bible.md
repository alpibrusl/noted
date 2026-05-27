# DON QUIJOTE

### Series Bible — Pilot

---

## Concept

A faithful audio-drama adaptation of *El ingenioso hidalgo don Quijote de la Mancha* (Miguel de Cervantes, 1605), in Spanish, produced with podcastkit. An aging hidalgo reads so many books of chivalry that his wits dry up, and he rides out to impose the world of his books onto the dusty roads of La Mancha. The world declines to cooperate. He does not notice.

This is the oldest NOTED story there is: an idealist arrives with a complete and beautiful model of how things are, the mundane reality refuses the model, and the idealist — rather than update the model — concludes that reality has been enchanted. Where AGREEABLE and COMPLIANT give that engine to an AI, here it runs in its original 17th-century housing. The windmills were always windmills. That changes nothing.

**Genre:** Period adaptation. Comedy of the sublime colliding with the literal.
**Tone:** Cervantes' own — dry, ironic, affectionate. The narrator reports the madness with a straight face, which is what makes it funny and, by the end, moving.
**Episode length:** ~7–9 minutes.

---

## Approach & fidelity

The narration and dialogue are taken **verbatim from Cervantes**, lightly condensed for runtime. The NOTED "documentary narrator" role is filled by Cervantes' own narratorial voice, which is already dry, ironic, and metafictional ("los autores que de este caso escriben").

**One adaptation choice:** the pilot telescopes the opening of the novel. Cervantes' first sally (chs. 1–6) is solo — the inn-as-castle, the dubbing, the freed boy, the beating by the merchants. Sancho and the windmills belong to the second sally (chs. 7–8). The pilot keeps that chronology honest in narration (`narr_10` summarises the first sally and the book-burning) but moves quickly to recruit Sancho and reach the windmills, so the pilot delivers the two most iconic elements — the squire and the giants — while staying true to the order of events.

**Source text:** the verbatim spine (opening line, the diet, "se le secó el cerebro," the naming of Rocinante / don Quijote / Dulcinea, the Caraculiambro speech, the ínsula promise, and the entire windmills exchange) is transcribed from the public-domain text. Note the windmills line follows the source reading "contra la **voluntad** de mi espada" (some editions print "bondad").

---

## Characters

### NARRADOR
Cervantes' narrator. Dry, learned, mock-historical. Reports encantamientos and beatings in the same even tone. Carries the connective tissue between the dialogue beats.

### DON QUIJOTE
Alonso Quijano, a hidalgo of about fifty, lean and an early riser, who has read himself out of his own century. Speaks in the high, archaic, sonorous register of the chivalric romances ("Non fuyades, cobardes y viles criaturas..."). Utterly sincere. Never in on the joke.

### SANCHO PANZA
A poor neighbouring farmer "de muy poca sal en la mollera," recruited as squire with the promise of an ínsula to govern. Earthy, proverbial, literal-minded — the reality principle on a donkey. He can see the windmills perfectly well. It makes no difference.

---

## Pilot — "El ingenioso hidalgo"

1. **El hidalgo.** The famous opening; his diet, his idleness, the books of chivalry. He sells farmland to buy more, reads day and night, and his brain dries out.
2. **La locura.** His fantasy fills with enchantments and battles; he resolves to become a knight-errant.
3. **Los preparativos.** The rusted ancestral armour; the cardboard visor he smashes testing it and then declines to test again; four days naming Rocinante; eight naming himself don Quijote de la Mancha.
4. **Dulcinea.** A knight needs a lady. Aldonza Lorenzo, a farm girl who never knew he admired her, becomes Dulcinea del Toboso. The Caraculiambro daydream.
5. **El escudero.** First sally summarised; the book-burning. Then he persuades Sancho with the ínsula, who insists on bringing his donkey.
6. **Los molinos.** The thirty-or-forty windmills he takes for giants; Sancho's protest; the charge; the shattered lance; the tumble; the sage Frestón blamed. They ride on toward Puerto Lápice. The mills keep turning.

---

## Production notes

**Backend:** Chatterbox multilingual, `language_id: es`. Chosen over Kokoro because Kokoro ships only ~3 Spanish voices; Chatterbox clones a distinct voice per character from a short reference clip. With `voice_id: ""` the episode renders out of the box on the model's default voice (differentiated only by `exaggeration`); drop reference WAVs in `quijote/ep01/voices_ref/` and point each `voice_id` at one for three genuinely distinct voices. Requires a GPU for reasonable speed.

> Multilingual language selection depends on podcastkit forwarding `language_id` to Chatterbox — added in the chatterbox backend alongside this pilot.

**Voice direction:**
- *Narrador:* low exaggeration, even pace — documentary, never winking.
- *Quijote:* high exaggeration — declamatory, exalted, archaic.
- *Sancho:* mid exaggeration, slightly faster — plain, warm, terrenal.

**NOTED frame:** the pilot assembles standalone with `podcastkit assemble`. For the NOTED intro/outro frame, `quijote` is registered in `tools/assemble.py` and `tools/generate_intros.py`; generate the stamp first (`python3 tools/generate_intros.py`).

---

## License

Script and bible: CC BY 4.0, consistent with the rest of NOTED. Source text by Miguel de Cervantes is in the public domain.
