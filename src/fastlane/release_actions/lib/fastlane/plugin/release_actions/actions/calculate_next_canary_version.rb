require 'fastlane/action'
require_relative '../helper/git'
require_relative '../helper/version/version'

module Fastlane
  module Actions
    class CalculateNextCanaryVersionAction < Action
      def self.run(params)
        version = Version.from(Git.last_tag)

        if version.prerelease?
          version = version.bump_prerelease
        else
          version = version.bump_patch
          version = version.as_prerelease(params[:prerelease_identifier])
        end

        version.to_s
      end

      def self.description
        'Actions to use your commit history to tag, generate changelogs, and push a release.'
      end

      def self.return_value
        'The next version calculated from the previous tag.'
      end

      def self.authors
        ['John Pignata', 'Ivan Artemiev']
      end

      def self.available_options
        [
          FastlaneCore::ConfigItem.new(
            key: :prerelease_identifier,
            env_name: 'PRERELEASE_IDENTIFIER',
            description: 'The pre-release identifier (e.g. unstable, dev, preview) for prerelease versions',
            type: String,
            optional: true,
            default_value: 'unstable'
          )
        ]
      end

      def self.is_supported?(platform)
        true
      end
    end
  end
end
