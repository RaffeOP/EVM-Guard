pragma solidity 0.8.20;

contract Escrow4063 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        supply += msg.value;
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }

    function ownerOf_() public view returns (address) { return owner; }
}
