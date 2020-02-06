from __future__ import unicode_literals
import os
import time
import json
import sys
import shutil
import logging
from converter import Converter, FFMpegConvertError
from extensions import valid_input_extensions, valid_output_extensions, valid_subtitle_extensions, subtitle_codec_extensions, valid_tagging_extensions
from babelfish import Language


class MkvtoMp4:
    def __init__(self, settings=None,
                 FFMPEG_PATH="FFMPEG.exe",
                 FFPROBE_PATH="FFPROBE.exe",
                 delete=True,
                 output_extension='mp4',
                 temp_extension=None,
                 output_dir=None,
                 relocate_moov=True,
                 output_format='mp4',
                 video_codec=['h264', 'x264'],
                 video_bitrate=None,
                 vcrf=None,
                 video_width=None,
                 video_profile=None,
                 h264_level=None,
                 qsv_decoder=True,
                 hevc_qsv_decoder=False,
                 dxva2_decoder=False,
                 audio_codec=['ac3'],
                 ignore_truehd=True,
                 audio_bitrate=256,
                 audio_filter=None,
                 audio_copyoriginal=False,
                 audio_first_language_track=False,
                 sort_by_language=False,
                 iOS=False,
                 iOSFirst=False,
                 iOSLast=False,
                 iOS_filter=None,
                 maxchannels=None,
                 aac_adtstoasc=False,
                 awl=None,
                 swl=None,
                 adl=None,
                 sdl=None,
                 scodec=['mov_text'],
                 subencoding='utf-8',
                 bad_internal_subtitle_codecs=[],
                 bad_external_subtitle_codecs=[],
                 downloadsubs=True,
                 processMP4=False,
                 forceConvert=False,
                 copyto=None,
                 moveto=None,
                 embedsubs=True,
                 embedonlyinternalsubs=True,
                 providers=['addic7ed', 'podnapisi', 'thesubdb', 'opensubtitles'],
                 permissions=int("777", 8),
                 pix_fmt=None,
                 logger=None,
                 threads='auto',
                 preopts=None,
                 postopts=None):
        # Setup Logging
        if logger:
            self.log = logger
        else:
            self.log = logging.getLogger(__name__)

        # Settings
        self.FFMPEG_PATH = FFMPEG_PATH
        self.FFPROBE_PATH = FFPROBE_PATH
        self.threads = threads
        self.delete = delete
        self.output_extension = output_extension
        self.temp_extension = temp_extension
        self.output_format = output_format
        self.output_dir = output_dir
        self.relocate_moov = relocate_moov
        self.processMP4 = processMP4
        self.forceConvert = forceConvert
        self.copyto = copyto
        self.moveto = moveto
        self.relocate_moov = relocate_moov
        self.permissions = permissions
        self.preopts = preopts
        self.postopts = postopts
        self.sort_by_language = sort_by_language
        # Video settings
        self.video_codec = video_codec
        self.video_bitrate = video_bitrate
        self.vcrf = vcrf
        self.video_width = video_width
        self.video_profile = video_profile
        self.h264_level = h264_level
        self.qsv_decoder = qsv_decoder
        self.hevc_qsv_decoder = hevc_qsv_decoder
        self.dxva2_decoder = dxva2_decoder
        self.pix_fmt = pix_fmt
        # Audio settings
        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate
        self.audio_filter = audio_filter
        self.iOS = iOS
        self.iOSFirst = iOSFirst
        self.iOSLast = iOSLast
        self.iOS_filter = iOS_filter
        self.maxchannels = maxchannels
        self.awl = awl
        self.adl = adl
        self.ignore_truehd = ignore_truehd
        self.aac_adtstoasc = aac_adtstoasc
        self.audio_copyoriginal = audio_copyoriginal
        self.audio_first_language_track = audio_first_language_track
        # Subtitle settings
        self.scodec = scodec
        self.swl = swl
        self.sdl = sdl
        self.downloadsubs = downloadsubs
        self.subproviders = providers
        self.embedsubs = embedsubs
        self.embedonlyinternalsubs = embedonlyinternalsubs
        self.subencoding = subencoding
        self.bad_internal_subtitle_codecs = bad_internal_subtitle_codecs
        self.bad_external_subtitle_codecs = bad_external_subtitle_codecs

        # Import settings
        if settings is not None:
            self.importSettings(settings)
        self.deletesubs = set()
        self.converter = Converter(self.FFMPEG_PATH, self.FFPROBE_PATH)

    def importSettings(self, settings):
        self.FFMPEG_PATH = settings.ffmpeg
        self.FFPROBE_PATH = settings.ffprobe
        self.threads = settings.threads
        self.delete = settings.delete
        self.output_extension = settings.output_extension
        self.temp_extension = settings.temp_extension
        self.output_format = settings.output_format
        self.output_dir = settings.output_dir
        self.relocate_moov = settings.relocate_moov
        self.processMP4 = settings.processMP4
        self.forceConvert = settings.forceConvert
        self.copyto = settings.copyto
        self.moveto = settings.moveto
        self.relocate_moov = settings.relocate_moov
        self.permissions = settings.permissions
        self.preopts = settings.preopts
        self.postopts = settings.postopts
        self.sort_by_language = settings.sort_by_language
        # Video settings
        self.video_codec = settings.vcodec
        self.video_bitrate = settings.vbitrate
        self.vcrf = settings.vcrf
        self.video_width = settings.vwidth
        self.video_profile = settings.vprofile
        self.h264_level = settings.h264_level
        self.qsv_decoder = settings.qsv_decoder
        self.hevc_qsv_decoder = settings.hevc_qsv_decoder
        self.dxva2_decoder = settings.dxva2_decoder
        self.pix_fmt = settings.pix_fmt
        # Audio settings
        self.audio_codec = settings.acodec
        self.audio_bitrate = settings.abitrate
        self.audio_filter = settings.afilter
        self.iOS = settings.iOS
        self.iOSFirst = settings.iOSFirst
        self.iOSLast = settings.iOSLast
        self.iOS_filter = settings.iOSfilter
        self.maxchannels = settings.maxchannels
        self.awl = settings.awl
        self.adl = settings.adl
        self.ignore_truehd = settings.ignore_truehd
        self.aac_adtstoasc = settings.aac_adtstoasc
        self.audio_copyoriginal = settings.audio_copyoriginal
        self.audio_first_language_track = settings.audio_first_language_track
        # Subtitle settings
        self.scodec = settings.scodec
        self.swl = settings.swl
        self.sdl = settings.sdl
        self.downloadsubs = settings.downloadsubs
        self.subproviders = settings.subproviders
        self.embedsubs = settings.embedsubs
        self.embedonlyinternalsubs = settings.embedonlyinternalsubs
        self.subencoding = settings.subencoding
        self.bad_internal_subtitle_codecs = settings.bad_internal_subtitle_codecs
        self.bad_external_subtitle_codecs = settings.bad_external_subtitle_codecs

        self.log.debug("Settings imported.")

    # Process a file from start to finish, with checking to make sure formats are compatible with selected settings
    def process(self, inputfile, reportProgress=False, original=None):

        self.log.debug("Process started.")

        delete = self.delete
        deleted = False
        options = None
        preopts = None
        postopts = None
        if not self.validSource(inputfile):
            return False

        if self.needProcessing(inputfile):
            options, preopts, postopts = self.generateOptions(inputfile, original=original)
            if not options:
                self.log.error("Error converting, inputfile %s had a valid extension but returned no data. Either the file does not exist, was unreadable, or was an incorrect format." % inputfile)
                return False

            try:
                self.log.info("Output Data")
                self.log.info(json.dumps(options, sort_keys=False, indent=4))
                self.log.info("Preopts")
                self.log.info(json.dumps(preopts, sort_keys=False, indent=4))
                self.log.info("Postopts")
                self.log.info(json.dumps(postopts, sort_keys=False, indent=4))
            except:
                self.log.exception("Unable to log options.")

            outputfile, inputfile = self.convert(inputfile, options, preopts, postopts, reportProgress)

            if not outputfile:
                self.log.debug("Error converting, no outputfile present.")
                return False

            self.log.debug("%s created from %s successfully." % (outputfile, inputfile))

        else:
            outputfile = inputfile
            if self.output_dir is not None:
                try:
                    outputfile = os.path.join(self.output_dir, os.path.split(inputfile)[1])
                    self.log.debug("Outputfile set to %s." % outputfile)
                    shutil.copy(inputfile, outputfile)
                except Exception as e:
                    self.log.exception("Error moving file to output directory.")
                    delete = False
            else:
                delete = False

        if delete:
            self.log.debug("Attempting to remove %s." % inputfile)
            if self.removeFile(inputfile):
                self.log.debug("%s deleted." % inputfile)
                deleted = True
            else:
                self.log.error("Couldn't delete %s." % inputfile)
        if self.downloadsubs:
            for subfile in self.deletesubs:
                self.log.debug("Attempting to remove subtitle %s." % subfile)
                if self.removeFile(subfile):
                    self.log.debug("Subtitle %s deleted." % subfile)
                else:
                    self.log.debug("Unable to delete subtitle %s." % subfile)
            self.deletesubs = set()

        dim = self.getDimensions(outputfile)
        input_extension = self.parseFile(inputfile)[2].lower()
        output_extension = self.parseFile(outputfile)[2].lower()

        return {'input': inputfile,
                'input_extension': input_extension,
                'input_deleted': deleted,
                'output': outputfile,
                'output_extension': output_extension,
                'options': options,
                'preopts': preopts,
                'postopts': postopts,
                'x': dim['x'],
                'y': dim['y']}

    # Determine if a source video file is in a valid format
    def validSource(self, inputfile):
        input_extension = self.parseFile(inputfile)[2]
        # Make sure the input_extension is some sort of recognized extension, and that the file actually exists
        if (input_extension.lower() in valid_input_extensions or input_extension.lower() in valid_output_extensions):
            if (os.path.isfile(inputfile)):
                self.log.debug("%s is valid." % inputfile)
                return True
            else:
                self.log.debug("%s not found." % inputfile)
                return False
        else:
            self.log.debug("%s is invalid with extension %s." % (inputfile, input_extension))
            return False

    # Determine if a file meets the criteria for processing
    def needProcessing(self, inputfile):
        input_extension = self.parseFile(inputfile)[2]
        # Make sure input and output extensions are compatible. If processMP4 is true, then make sure the input extension is a valid output extension and allow to proceed as well
        if (input_extension.lower() in valid_input_extensions or (self.processMP4 is True and input_extension.lower() in valid_output_extensions)) and self.output_extension.lower() in valid_output_extensions:
            self.log.debug("%s needs processing." % inputfile)
            return True
        else:
            self.log.debug("%s does not need processing." % inputfile)
            return False

    # Get values for width and height to be passed to the tagging classes for proper HD tags
    def getDimensions(self, inputfile):
        if self.validSource(inputfile):
            info = self.converter.probe(inputfile)

            self.log.debug("Height: %s" % info.video.video_height)
            self.log.debug("Width: %s" % info.video.video_width)

            return {'y': info.video.video_height,
                    'x': info.video.video_width}

        return {'y': 0,
                'x': 0}

    # Estimate the video bitrate
    def estimateVideoBitrate(self, info):
        total_bitrate = info.format.bitrate
        audio_bitrate = 0
        for a in info.audio:
            audio_bitrate += a.bitrate

        self.log.debug("Total bitrate is %s." % info.format.bitrate)
        self.log.debug("Total audio bitrate is %s." % audio_bitrate)
        self.log.debug("Estimated video bitrate is %s." % (total_bitrate - audio_bitrate))
        return ((total_bitrate - audio_bitrate) / 1000) * .95

    # Generate a JSON formatter dataset with the input and output information and ffmpeg command for a theoretical conversion
    def jsonDump(self, inputfile, original=None):
        dump = {}
        dump["input"] = self.generateSourceDict(inputfile)
        dump["output"], dump["preopts"], dump["postopts"] = self.generateOptions(inputfile, original)
        parsed = self.converter.parse_options(dump["output"])
        input_dir, filename, input_extension = self.parseFile(inputfile)
        outputfile, output_extension = self.getOutputFile(input_dir, filename, input_extension)
        cmds = self.converter.ffmpeg.generateCommands(inputfile, outputfile, parsed, dump["preopts"], dump["postopts"])
        dump["ffmpeg_command"] = " ".join(str(item) for item in cmds)
        return json.dumps(dump, sort_keys=False, indent=4)

    # Generate a dict of data about a source file
    def generateSourceDict(self, inputfile):
        output = {}
        input_dir, filename, input_extension = self.parseFile(inputfile)
        output['extension'] = input_extension
        probe = self.converter.probe(inputfile)
        if probe:
            output.update(probe.toJson())
        else:
            output['error'] = "Invalid input, unable to read"
        return output

    # Generate a dict of options to be passed to FFMPEG based on selected settings and the source file parameters and streams
    def generateOptions(self, inputfile, original=None):
        # Get path information from the input file
        input_dir, filename, input_extension = self.parseFile(inputfile)

        info = self.converter.probe(inputfile)
        if not info:
            self.log.error("FFProbe returned no value for inputfile %s (exists: %s), either the file does not exist or is not a format FFPROBE can read." % (inputfile, os.path.exists(inputfile)))
            return None, None, None

        self.log.info("Input Data")
        self.log.info(json.dumps(info.toJson(), sort_keys=False, indent=4))
        # Video stream
        self.log.info("Reading video stream.")
        self.log.info("Video codec detected: %s." % info.video.codec)

        vdebug = "base"
        try:
            vbr = self.estimateVideoBitrate(info)
        except:
            vbr = info.format.bitrate / 1000

        if info.video.codec.lower() in self.video_codec:
            vcodec = 'copy'
        else:
            vcodec = self.video_codec[0]
        vbitrate = self.video_bitrate if self.video_bitrate else vbr

        self.log.info("Pix Fmt: %s." % info.video.pix_fmt)
        if self.pix_fmt and info.video.pix_fmt.lower() not in self.pix_fmt:
            self.log.debug("Overriding video pix_fmt. Codec cannot be copied because pix_fmt is not approved.")
            vdebug = vdebug + ".pix_fmt"
            vcodec = self.video_codec[0]
            pix_fmt = self.pix_fmt[0]
            if self.video_profile:
                vprofile = self.video_profile[0]
        elif self.pix_fmt:
            pix_fmt = self.pix_fmt[0]
        else:
            pix_fmt = None

        if self.video_bitrate is not None and vbr > self.video_bitrate:
            self.log.debug("Overriding video bitrate. Codec cannot be copied because video bitrate is too high.")
            vdebug = vdebug + ".video-bitrate"
            vcodec = self.video_codec[0]
            vbitrate = self.video_bitrate

        if self.video_width is not None and self.video_width < info.video.video_width:
            self.log.debug("Video width is over the max width, it will be downsampled. Video stream can no longer be copied.")
            vdebug = vdebug + ".video-max-width"
            vcodec = self.video_codec[0]
            vwidth = self.video_width
        else:
            vwidth = self.video_width

        if '264' in info.video.codec.lower() and self.h264_level and info.video.video_level and (info.video.video_level / 10 > self.h264_level):
            self.log.info("Video level %0.1f. Codec cannot be copied because video level is too high." % (info.video.video_level / 10))
            vdebug = vdebug + ".h264-max-level"
            vcodec = self.video_codec[0]

        self.log.debug("Video codec: %s." % vcodec)
        self.log.debug("Video bitrate: %s." % vbitrate)

        self.log.info("Profile: %s." % info.video.profile)
        if self.video_profile and info.video.profile.lower().replace(" ", "") not in self.video_profile:
            self.log.debug("Video profile is not supported. Video stream can no longer be copied.")
            vdebug = vdebug + ".video-profile"
            vcodec = self.video_codec[0]
            vprofile = self.video_profile[0]
            if self.pix_fmt:
                pix_fmt = self.pix_fmt[0]
        elif self.video_profile:
            vprofile = self.video_profile[0]
        else:
            vprofile = None

        # Audio streams
        self.log.info("Reading audio streams.")

        overrideLang = (self.awl is not None)
        # Loop through audio tracks and clean up language metadata by standardizing undefined languages and applying the ADL setting
        for a in info.audio:
            try:
                if a.metadata['language'].strip() == "" or a.metadata['language'] is None:
                    a.metadata['language'] = 'und'
            except KeyError:
                a.metadata['language'] = 'und'

            # Set undefined language to default language if specified
            if self.adl is not None and a.metadata['language'] == 'und':
                self.log.debug("Undefined language detected, defaulting to [%s]." % self.adl)
                a.metadata['language'] = self.adl

            if (self.awl and a.metadata['language'].lower() in self.awl):
                overrideLang = False

        if overrideLang:
            self.awl = None
            self.log.info("No audio streams detected in any appropriate language, relaxing restrictions so there will be some audio stream present.")

        # Reorder audio tracks based on the approved audio languages, mirrors the order present from the options
        audio_streams = info.audio
        if self.sort_by_language and self.awl:
            self.log.debug("Reordering audio tracks to be in accordance with approved languages [sort-tracks-by-language].")
            audio_streams.sort(key=lambda x: self.awl[::-1].index(x.metadata['language']) if x.metadata['language'] in self.awl else -1)
            audio_streams.reverse()

        audio_settings = {}
        blocked_audio_languages = []
        l = 0

        for a in audio_streams:
            self.log.info("Audio detected for stream #%s: %s [%s]." % (a.index, a.codec, a.metadata['language']))

            if self.output_extension in valid_tagging_extensions and a.codec.lower() == 'truehd' and self.ignore_truehd and len(info.audio) > 1:  # Need to skip it early so that it flags the next track as default.
                self.log.info("MP4 containers do not support truehd audio, and converting it is inconsistent due to video/audio sync issues. Skipping stream %s as typically the 2nd audio track is the AC3 core of the truehd stream [ignore-truehd]." % a.index)
                continue

            # Proceed if no whitelist is set, or if the language is in the whitelist
            iosdata = None
            if self.awl is None or (a.metadata['language'].lower() in self.awl and a.metadata['language'].lower() not in blocked_audio_languages):
                # Create iOS friendly audio stream if the default audio stream has too many channels (iOS only likes AAC stereo)
                if self.iOS and a.audio_channels > 2:
                    iOSbitrate = 256 if (self.audio_bitrate * 2) > 256 else (self.audio_bitrate * 2)

                    # Bitrate calculations/overrides
                    if self.audio_bitrate is 0:
                        self.log.debug("Attempting to set ios stream bitrate based on source stream bitrate.")
                        try:
                            iOSbitrate = ((a.bitrate / 1000) / a.audio_channels) * 2
                        except:
                            self.log.warning("Unable to determine iOS audio bitrate from source stream %s, defaulting to 256 per channel." % a.index)
                            iOSbitrate = audio_channels * 256

                    self.log.debug("Audio codec: %s." % self.iOS[0])
                    self.log.debug("Channels: 2.")
                    self.log.debug("Filter: %s." % self.iOS_filter)
                    self.log.debug("Bitrate: %s." % iOSbitrate)
                    self.log.debug("Language: %s." % a.metadata['language'])
                    iosdata = {
                        'map': a.index,
                        'codec': self.iOS[0],
                        'channels': 2,
                        'bitrate': iOSbitrate,
                        'filter': self.iOS_filter,
                        'language': a.metadata['language'],
                        'disposition': 'none',
                        'debug': 'ios-audio'
                    }
                    if not self.iOSLast:
                        self.log.info("Creating %s audio stream %d from source audio stream %d [iOS-audio]." % (self.iOS[0], l, a.index))
                        audio_settings.update({l: iosdata})
                        l += 1

                adebug = "base"
                # If the iOS audio option is enabled and the source audio channel is only stereo, the additional iOS channel will be skipped and a single AAC 2.0 channel will be made regardless of codec preference to avoid multiple stereo channels
                if self.iOS and a.audio_channels <= 2:
                    self.log.debug("Overriding default channel settings because iOS audio is enabled but the source is stereo [iOS-audio].")
                    acodec = 'copy' if a.codec in self.iOS else self.iOS[0]
                    audio_channels = a.audio_channels
                    afilter = self.iOS_filter
                    abitrate = a.audio_channels * 128 if (a.audio_channels * self.audio_bitrate) > (a.audio_channels * 128) else (a.audio_channels * self.audio_bitrate)
                    adebug = adebug + ".ios-audio"
                else:
                    # If desired codec is the same as the source codec, copy to avoid quality loss
                    acodec = 'copy' if a.codec.lower() in self.audio_codec else self.audio_codec[0]
                    afilter = self.audio_filter
                    # Audio channel adjustments
                    if self.maxchannels and a.audio_channels > self.maxchannels:
                        self.log.debug("Audio source exceeds maximum channels, can not be copied. Settings channels to %d [audio-max-channels]." % self.maxchannels)
                        adebug = adebug + ".audio-max-channels"
                        audio_channels = self.maxchannels
                        acodec = self.audio_codec[0]
                        abitrate = self.maxchannels * self.audio_bitrate
                    else:
                        audio_channels = a.audio_channels
                        abitrate = a.audio_channels * self.audio_bitrate

                # Bitrate calculations/overrides
                if self.audio_bitrate is 0:
                    self.log.debug("Attempting to set bitrate based on source stream bitrate.")
                    try:
                        abitrate = ((a.bitrate / 1000) / a.audio_channels) * audio_channels
                    except:
                        self.log.warning("Unable to determine audio bitrate from source stream %s, defaulting to 256 per channel." % a.index)
                        abitrate = audio_channels * 256

                self.log.debug("Audio codec: %s." % acodec)
                self.log.debug("Channels: %s." % audio_channels)
                self.log.debug("Bitrate: %s." % abitrate)
                self.log.debug("Language: %s" % a.metadata['language'])
                self.log.debug("Filter: %s" % afilter)
                self.log.debug("Debug: %s" % adebug)

                # If the iOSFirst option is enabled, disable the iOS option after the first audio stream is processed
                if self.iOS and self.iOSFirst:
                    self.log.debug("Not creating any additional iOS audio streams [iOS-first-track-only].")
                    self.iOS = False

                self.log.info("Creating %s audio stream %d from source stream %d." % (acodec, l, a.index))
                audio_settings.update({l: {
                    'map': a.index,
                    'codec': acodec,
                    'channels': audio_channels,
                    'bitrate': abitrate,
                    'filter': afilter,
                    'language': a.metadata['language'],
                    'disposition': 'none',
                    'debug': adebug
                }})

                if acodec == 'copy' and a.codec == 'aac' and self.aac_adtstoasc:
                    audio_settings[l]['bsf'] = 'aac_adtstoasc'
                l += 1

                # Add the iOS track last instead
                if self.iOSLast and iosdata:
                    self.log.info("Creating %s audio stream %d from source audio stream %d [iOS-audio]." % (self.iOS[0], l, a.index))
                    audio_settings.update({l: iosdata})
                    l += 1

                if self.audio_copyoriginal and acodec != 'copy':
                    self.log.info("Copying to audio stream %d from source stream %d format %s [audio-copy-original]" % (l, a.index, a.codec))
                    audio_settings.update({l: {
                        'map': a.index,
                        'codec': 'copy',
                        'language': a.metadata['language'],
                        'disposition': 'none',
                        'debug': 'audio-copy-original'
                    }})
                    l += 1

                # Remove the language if we only want the first track from a given language
                if self.audio_first_language_track:
                    try:
                        blocked_audio_languages.append(a.metadata['language'].lower())
                        self.log.debug("Removing language from whitelist to prevent multiple tracks of the same: %s." % a.metadata['language'])
                    except:
                        self.log.error("Unable to remove language %s from whitelist." % a.metadata['language'])

        # Audio Default
        if len(audio_settings) > 0 and self.adl:
            try:
                default_track = [x for x in audio_settings.values() if x['language'] == self.adl][0]
                default_track['disposition'] = 'default'
            except:
                audio_settings[0]['disposition'] = 'default'
        else:
            self.log.error("Audio language array is empty.")

        # Prep subtitle streams by cleaning up languages and setting SDL6
        for s in info.subtitle:
            try:
                if s.metadata['language'].strip() == "" or s.metadata['language'] is None:
                    s.metadata['language'] = 'und'
            except KeyError:
                s.metadata['language'] = 'und'

            self.log.info("Subtitle detected for stream #%s: %s [%s]." % (s.index, s.codec, s.metadata['language']))

            # Set undefined language to default language if specified
            if self.sdl is not None and s.metadata['language'] == 'und':
                self.log.debug("Undefined language detected, defaulting to [%s]." % self.sdl)
                s.metadata['language'] = self.sdl

        # Reorder subtitle tracks based on the approved languages, mirrors the order present from the options
        subtitle_streams = info.subtitle
        if self.sort_by_language and self.swl:
            self.log.debug("Reordering subtitle tracks to be in accordance with approved languages [sort-tracks-by-language].")
            subtitle_streams.sort(key=lambda x: self.swl[::-1].index(x.metadata['language']) if x.metadata['language'] in self.swl else -1)
            subtitle_streams.reverse()

        subtitle_settings = {}
        l = 0
        self.log.info("Reading subtitle streams.")
        for s in subtitle_streams:
            self.log.info("Subtitle detected for stream #%s: %s [%s]." % (s.index, s.codec, s.metadata['language']))

            # Make sure its not an image based codec
            if self.embedsubs and s.codec.lower() not in self.bad_internal_subtitle_codecs:
                # Proceed if no whitelist is set, or if the language is in the whitelist
                if self.swl is None or s.metadata['language'].lower() in self.swl:
                    subtitle_settings.update({l: {
                        'map': s.index,
                        'codec': self.scodec[0],
                        'language': s.metadata['language'],
                        'encoding': self.subencoding,
                        'disposition': 'none',
                        'debug': 'base',
                        # 'forced': s.sub_forced,
                        # 'default': s.sub_default
                    }})
                    self.log.info("Creating %s subtitle stream %d from source stream %d." % (self.scodec[0], l, s.index))
                    l = l + 1
            elif not self.embedsubs and s.codec.lower() not in self.bad_external_subtitle_codecs:
                if self.swl is None or s.metadata['language'].lower() in self.swl:

                    for codec in self.scodec:
                        ripsub = {0: {
                            'map': s.index,
                            'codec': codec,
                            'language': s.metadata['language'],
                            'debug': "base-rip"
                        }}
                        options = {
                            'format': codec,
                            'subtitle': ripsub,
                        }

                        try:
                            extension = subtitle_codec_extensions[codec]
                        except:
                            self.log.info("Wasn't able to determine subtitle file extension, defaulting to '.srt'.")
                            extension = 'srt'

                        forced = ".forced" if s.sub_forced else ""

                        input_dir, filename, input_extension = self.parseFile(inputfile)
                        output_dir = input_dir if self.output_dir is None else self.output_dir
                        outputfile = os.path.join(output_dir, filename + "." + s.metadata['language'] + forced + "." + extension)

                        i = 2
                        while os.path.isfile(outputfile):
                            self.log.debug("%s exists, appending %s to filename." % (outputfile, i))
                            outputfile = os.path.join(output_dir, filename + "." + s.metadata['language'] + forced + "." + str(i) + "." + extension)
                            i += 1
                        try:
                            self.log.info("Ripping %s subtitle from source stream %s into external file." % (s.metadata['language'], s.index))
                            conv = self.converter.convert(inputfile, outputfile, options, timeout=None)
                            for timecode in conv:
                                pass

                            self.log.info("%s created." % outputfile)
                        except FFMpegConvertError:
                            self.log.error("Unabled to create external %s subtitle file for stream %s, may be an incompatible format." % (extension, s.index))
                            self.removeFile(outputfile)
                            continue
                        except:
                            self.log.exception("Unabled to create external subtitle file for stream %s." % (s.index))

                        try:
                            os.chmod(outputfile, self.permissions)  # Set permissions of newly created file
                        except:
                            self.log.exception("Unable to set new file permissions.")

        # Attempt to download subtitles if they are missing using subliminal
        languages = set()
        try:
            if self.swl:
                for alpha3 in self.swl:
                    languages.add(Language(alpha3))
            elif self.sdl:
                languages.add(Language(self.sdl))
            else:
                self.downloadsubs = False
                self.log.error("No valid subtitle language specified, cannot download subtitles.")
        except:
            self.log.exception("Unable to verify subtitle languages for download.")
            self.downloadsubs = False

        if self.downloadsubs:
            import subliminal
            self.log.info("Attempting to download subtitles.")

            # Attempt to set the dogpile cache
            try:
                subliminal.region.configure('dogpile.cache.memory')
            except:
                pass

            try:
                video = subliminal.scan_video(os.path.abspath(inputfile), subtitles=True, embedded_subtitles=True)
                subtitles = subliminal.download_best_subtitles([video], languages, hearing_impaired=False, providers=self.subproviders)
                try:
                    subliminal.save_subtitles(video, subtitles[video])
                except:
                    # Support for older versions of subliminal
                    subliminal.save_subtitles(subtitles)
                    self.log.info("Please update to the latest version of subliminal.")
            except Exception as e:
                self.log.info("Unable to download subtitles.", exc_info=True)
                self.log.debug("Unable to download subtitles.", exc_info=True)
        # External subtitle import
        if self.embedsubs and not self.embedonlyinternalsubs:  # Don't bother if we're not embeddeding subtitles and external subtitles
            src = 1  # FFMPEG input source number
            for dirName, subdirList, fileList in os.walk(input_dir):
                for fname in fileList:
                    subname, subextension = os.path.splitext(fname)
                    # Watch for appropriate file extension
                    if subextension[1:] in valid_subtitle_extensions:
                        x, lang = os.path.splitext(subname)
                        lang = lang[1:]
                        # Using bablefish to convert a 2 language code to a 3 language code
                        if len(lang) is 2:
                            try:
                                babel = Language.fromalpha2(lang)
                                lang = babel.alpha3
                            except:
                                pass
                        # If subtitle file name and input video name are the same, proceed
                        if x == filename:
                            self.log.info("External %s subtitle file detected." % lang)
                            if self.swl is None or lang in self.swl:

                                self.log.info("Creating subtitle stream %s by importing %s." % (l, fname))

                                subtitle_settings.update({l: {
                                    'path': os.path.join(dirName, fname),
                                    'source': src,
                                    'map': 0,
                                    'codec': 'mov_text',
                                    'disposition': 'none',
                                    'language': lang}})

                                self.log.debug("Path: %s." % os.path.join(dirName, fname))
                                self.log.debug("Source: %s." % src)
                                self.log.debug("Codec: mov_text.")
                                self.log.debug("Langauge: %s." % lang)

                                l = l + 1
                                src = src + 1

                                self.deletesubs.add(os.path.join(dirName, fname))

                            else:
                                self.log.info("Ignoring %s external subtitle stream due to language %s." % (fname, lang))

        # Subtitle Default
        if len(subtitle_settings) > 0 and self.sdl:
            try:
                default_track = [x for x in subtitle_settings.values() if x['language'] == self.sdl][0]
                default_track['disposition'] = 'default'
            except:
                subtitle_settings[0]['disposition'] = 'default'
        else:
            self.log.warning("Subtitle stream array is empty.")

        # Collect all options
        options = {
            'format': self.output_format,
            'video': {
                'codec': vcodec,
                'map': info.video.index,
                'bitrate': vbitrate,
                'level': self.h264_level,
                'profile': vprofile,
                'pix_fmt': pix_fmt,
                'debug': vdebug
            },
            'audio': audio_settings,
            'subtitle': subtitle_settings
        }

        preopts = []
        postopts = ['-threads', self.threads]

        # If a CRF option is set, override the determine bitrate
        if self.vcrf:
            del options['video']['bitrate']
            options['video']['crf'] = self.vcrf

        if len(options['subtitle']) > 0:
            preopts.append('-fix_sub_duration')

        if self.preopts:
            preopts.extend(self.preopts)

        if self.postopts:
            postopts.extend(self.postopts)

        if self.dxva2_decoder:  # DXVA2 will fallback to CPU decoding when it hits a file that it cannot handle, so we don't need to check if the file is supported.
            preopts.extend(['-hwaccel', 'dxva2'])
        elif info.video.codec.lower() == "hevc" and self.hevc_qsv_decoder:
            preopts.extend(['-vcodec', 'hevc_qsv'])
        elif vcodec == "h264qsv" and info.video.codec.lower() == "h264" and self.qsv_decoder and (info.video.video_level / 10) < 5:
            preopts.extend(['-vcodec', 'h264_qsv'])

        # Add width option
        if vwidth:
            options['video']['width'] = vwidth

        # HEVC Tagging for copied streams
        if info.video.codec.lower() in ['x265', 'h265', 'hevc'] and vcodec == 'copy':
            postopts.extend(['-tag:v', 'hvc1'])
            self.log.info("Tagging copied video stream as hvc1")

        return options, preopts, postopts

    def getOutputFile(self, input_dir, filename, input_extension):
        output_dir = input_dir if self.output_dir is None else self.output_dir
        output_extension = self.temp_extension if self.temp_extension else self.output_extension

        self.log.debug("Input directory: %s." % input_dir)
        self.log.debug("File name: %s." % filename)
        self.log.debug("Input extension: %s." % input_extension)
        self.log.debug("Output directory: %s." % output_dir)
        self.log.debug("Output extension: %s." % output_dir)

        try:
            outputfile = os.path.join(output_dir.decode(sys.getfilesystemencoding()), filename.decode(sys.getfilesystemencoding()) + "." + output_extension).encode(sys.getfilesystemencoding())
        except:
            outputfile = os.path.join(output_dir, filename + "." + output_extension)

        self.log.debug("Output file: %s." % outputfile)
        return outputfile, output_dir

    # Encode a new file based on selected options, built in naming conflict resolution
    def convert(self, inputfile, options, preopts, postopts, reportProgress=False):
        self.log.info("Starting conversion.")
        input_dir, filename, input_extension = self.parseFile(inputfile)
        originalinputfile = inputfile
        outputfile, output_dir = self.getOutputFile(input_dir, filename, input_extension)
        finaloutputfile = outputfile[:]

        self.log.debug("Final output file: %s." % finaloutputfile)

        if len(options['audio']) == 0:
            self.error.info("Conversion has no audio tracks, aborting")
            return inputfile, ""

        if not self.forceConvert and self.output_extension == input_extension and len([x for x in [options['video']] + [x for x in options['audio'].values()] + [x for x in options['subtitle'].values()] if x['codec'] != 'copy']) == 0:
            self.log.info("Input and output extensions match and every codec is copy, this file probably doesn't need conversion, returning.")
            self.log.info(inputfile)
            return inputfile, ""

        if os.path.abspath(inputfile) == os.path.abspath(finaloutputfile):
            self.log.debug("Inputfile and final outputfile are the same.")
            try:
                os.rename(inputfile, inputfile + ".original")
                inputfile = inputfile + ".original"
                self.log.debug("Renaming original file to %s." % inputfile)
            except:
                i = 2
                while os.path.isfile(outputfile):
                    outputfile = os.path.join(output_dir, filename + "(" + str(i) + ")." + self.output_extension)
                    i += i
                self.log.debug("Unable to rename inputfile. Setting output file name to %s." % outputfile)

        conv = self.converter.convert(inputfile, outputfile, options, timeout=None, preopts=preopts, postopts=postopts)

        try:
            for timecode in conv:
                if reportProgress:
                    try:
                        sys.stdout.write('\r')
                        sys.stdout.write('[{0}] {1}%'.format('#' * (timecode / 10) + ' ' * (10 - (timecode / 10)), timecode))
                    except:
                        sys.stdout.write(str(timecode))
                    sys.stdout.flush()

            self.log.info("%s created." % outputfile)

            try:
                os.chmod(outputfile, self.permissions)  # Set permissions of newly created file
            except:
                self.log.exception("Unable to set new file permissions.")

        except FFMpegConvertError as e:
            self.log.exception("Error converting file, FFMPEG error.")
            self.log.error(e.cmd)
            self.log.error(e.output)
            if os.path.isfile(outputfile):
                self.removeFile(outputfile)
                self.log.error("%s deleted." % outputfile)
            outputfile = None
            os.rename(inputfile, originalinputfile)
            raise Exception("FFMpegConvertError")

        if outputfile != finaloutputfile:
            self.log.debug("Outputfile and finaloutputfile are different, temporary extension used, attempting to rename to final extension")
            try:
                os.rename(outputfile, finaloutputfile)
            except:
                self.log.exception("Unable to rename output file to its final destination file extension")
                finaloutputfile = outputfile

        return finaloutputfile, inputfile

    # Break apart a file path into the directory, filename, and extension
    def parseFile(self, path):
        path = os.path.abspath(path)
        input_dir, filename = os.path.split(path)
        filename, input_extension = os.path.splitext(filename)
        input_extension = input_extension[1:]
        return input_dir, filename, input_extension

    # Process a file with QTFastStart, removing the original file
    def QTFS(self, inputfile):
        input_dir, filename, input_extension = self.parseFile(inputfile)
        temp_ext = '.QTFS'
        # Relocate MOOV atom to the very beginning. Can double the time it takes to convert a file but makes streaming faster
        if self.parseFile(inputfile)[2] in valid_output_extensions and os.path.isfile(inputfile) and self.relocate_moov:
            from qtfaststart import processor, exceptions

            self.log.info("Relocating MOOV atom to start of file.")

            try:
                outputfile = inputfile.decode(sys.getfilesystemencoding()) + temp_ext
            except:
                outputfile = inputfile + temp_ext

            # Clear out the temp file if it exists
            if os.path.exists(outputfile):
                self.removeFile(outputfile, 0, 0)

            try:
                processor.process(inputfile, outputfile)
                try:
                    os.chmod(outputfile, self.permissions)
                except:
                    self.log.exception("Unable to set file permissions.")
                # Cleanup
                if self.removeFile(inputfile, replacement=outputfile):
                    return outputfile
                else:
                    self.log.error("Error cleaning up QTFS temp files.")
                    return False
            except exceptions.FastStartException:
                self.log.warning("QT FastStart did not run - perhaps moov atom was at the start already.")
                return inputfile

    # Makes additional copies of the input file in each directory specified in the copy_to option
    def replicate(self, inputfile, relativePath=None):
        files = [inputfile]

        if self.copyto:
            self.log.debug("Copyto option is enabled.")
            for d in self.copyto:
                if (relativePath):
                    d = os.path.join(d, relativePath)
                    if not os.path.exists(d):
                        os.makedirs(d)
                try:
                    shutil.copy(inputfile, d)
                    self.log.info("%s copied to %s." % (inputfile, d))
                    files.append(os.path.join(d, os.path.split(inputfile)[1]))
                except Exception as e:
                    self.log.exception("First attempt to copy the file has failed.")
                    try:
                        if os.path.exists(inputfile):
                            self.removeFile(inputfile, 0, 0)
                        try:
                            shutil.copy(inputfile.decode(sys.getfilesystemencoding()), d)
                        except:
                            shutil.copy(inputfile, d)
                        self.log.info("%s copied to %s." % (inputfile, d))
                        files.append(os.path.join(d, os.path.split(inputfile)[1]))
                    except Exception as e:
                        self.log.exception("Unable to create additional copy of file in %s." % (d))

        if self.moveto:
            self.log.debug("Moveto option is enabled.")
            moveto = os.path.join(self.moveto, relativePath) if relativePath else self.moveto
            if not os.path.exists(moveto):
                os.makedirs(moveto)
            try:
                shutil.move(inputfile, moveto)
                self.log.info("%s moved to %s." % (inputfile, moveto))
                files[0] = os.path.join(moveto, os.path.basename(inputfile))
            except Exception as e:
                self.log.exception("First attempt to move the file has failed.")
                try:
                    if os.path.exists(inputfile):
                        self.removeFile(inputfile, 0, 0)
                    shutil.move(inputfile.decode(sys.getfilesystemencoding()), moveto)
                    self.log.info("%s moved to %s." % (inputfile, moveto))
                    files[0] = os.path.join(moveto, os.path.basename(inputfile))
                except Exception as e:
                    self.log.exception("Unable to move %s to %s" % (inputfile, moveto))
        for filename in files:
            self.log.debug("Final output file: %s." % filename)
        return files

    # Robust file removal function, with options to retry in the event the file is in use, and replace a deleted file
    def removeFile(self, filename, retries=2, delay=10, replacement=None):
        for i in range(retries + 1):
            try:
                # Make sure file isn't read-only
                os.chmod(filename, int("0777", 8))
            except:
                self.log.debug("Unable to set file permissions before deletion. This is not always required.")
            try:
                if os.path.exists(filename):
                    os.remove(filename)
                # Replaces the newly deleted file with another by renaming (replacing an original with a newly created file)
                if replacement is not None:
                    os.rename(replacement, filename)
                    filename = replacement
                break
            except:
                self.log.exception("Unable to remove or replace file %s." % filename)
                if delay > 0:
                    self.log.debug("Delaying for %s seconds before retrying." % delay)
                    time.sleep(delay)
        return False if os.path.isfile(filename) else True
