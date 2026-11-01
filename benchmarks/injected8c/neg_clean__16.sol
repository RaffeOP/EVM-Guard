pragma solidity 0.8.20;

contract Bank4719 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        supply += msg.value;
    }

    function ownerOf_() public view returns (address) { return owner; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
