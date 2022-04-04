import copy
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Type

import sanitize_filename

from ytdl_subscribe.utils.enums import SubscriptionSourceName
from ytdl_subscribe.validators.base.strict_dict_validator import StrictDictValidator
from ytdl_subscribe.validators.base.string_formatter_validator import (
    DictFormatterValidator,
)
from ytdl_subscribe.validators.base.validators import DictValidator
from ytdl_subscribe.validators.config.metadata_options.metadata_options_validator import (
    MetadataOptionsValidator,
)
from ytdl_subscribe.validators.config.output_options.output_options_validator import (
    OutputOptionsValidator,
)
from ytdl_subscribe.validators.config.sources.soundcloud_validators import (
    SoundcloudSourceValidator,
)
from ytdl_subscribe.validators.config.sources.source_validator import SourceValidator
from ytdl_subscribe.validators.config.sources.youtube_validators import (
    YoutubeSourceValidator,
)
from ytdl_subscribe.validators.exceptions import ValidationException


class YTDLOptionsValidator(DictValidator):
    pass


class OverridesValidator(DictFormatterValidator):
    @property
    def dict(self) -> dict:
        """For overrides, create sanitized versions of each entry for convenience"""
        output_dict = copy.deepcopy(super().dict)
        for key in self.keys:
            output_dict[f"sanitized_{key}"] = sanitize_filename.sanitize(
                output_dict[key]
            )

        return output_dict


class PresetValidator(StrictDictValidator):
    required_keys = {"output_options, metadata_options"}
    optional_keys = {
        "ytdl_options",
        "overrides",
        *SubscriptionSourceName.all(),
    }

    subscription_source_validator_mapping: Dict[str, Type[SourceValidator]] = {
        SubscriptionSourceName.SOUNDCLOUD: SoundcloudSourceValidator,
        SubscriptionSourceName.YOUTUBE: YoutubeSourceValidator,
    }

    def __validate_and_get_subscription_source(self) -> Tuple[str, SourceValidator]:
        subscription_source: Optional[SourceValidator] = None
        subscription_source_name: Optional[str] = None

        for key in self.keys:
            if key in SubscriptionSourceName.all() and subscription_source:
                raise ValidationException(
                    f"'{self.name}' can only have one of the following sources: {SubscriptionSourceName.pretty_all()}"
                )

            if key in self.subscription_source_validator_mapping:
                subscription_source_name = key
                subscription_source = self.validate_key(
                    key=key, validator=self.subscription_source_validator_mapping[key]
                )

        # If subscription source was not set, error
        if not subscription_source:
            raise ValidationException(
                f"'{self.name} must have one of the following sources: {SubscriptionSourceName.pretty_all()}"
            )

        return subscription_source_name, subscription_source

    def __init__(self, name: str, value: Any):
        super().__init__(name=name, value=value)
        (
            self.subscription_source_name,
            self.subscription_source,
        ) = self.__validate_and_get_subscription_source()

        self.output_options = self.validate_key(
            key="output_options",
            validator=OutputOptionsValidator,
        )
        self.metadata_options = self.validate_key(
            key="metadata_options", validator=MetadataOptionsValidator
        )

        self.ytdl_options = self.validate_key(
            key="ytdl_options", validator=YTDLOptionsValidator, default={}
        )

        self.overrides = self.validate_key(
            key="overrides", validator=OverridesValidator, default={}
        )
