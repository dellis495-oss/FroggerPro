/* Copyright (C) 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioTrack;

/** Two-second low-amplitude music-route probe; never changes system volume. */
public final class FroggerAudioProbe {
    public static void main(String[] args) throws Exception {
        final int rate = 48000;
        short[] samples = new short[rate * 2 * 2];
        for (int frame = 0; frame < rate * 2; frame++) {
            short value = (short) (3000 * Math.sin(2 * Math.PI * 440 * frame / rate));
            samples[frame * 2] = samples[frame * 2 + 1] = value;
        }
        AudioTrack track = new AudioTrack.Builder()
                .setAudioAttributes(new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build())
                .setAudioFormat(new AudioFormat.Builder().setSampleRate(rate)
                        .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO).build())
                .setTransferMode(AudioTrack.MODE_STATIC)
                .setBufferSizeInBytes(samples.length * 2).build();
        try {
            System.out.println("state=" + track.getState());
            System.out.println("written_samples=" + track.write(samples, 0, samples.length));
            track.play();
            Thread.sleep(2300);
            System.out.println("rendered_frames=" + track.getPlaybackHeadPosition());
            System.out.println("routed_device=" + track.getRoutedDevice());
        } finally {
            track.release();
        }
    }
}
