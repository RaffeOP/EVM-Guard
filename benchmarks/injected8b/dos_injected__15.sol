pragma solidity 0.8.20;

contract Fund5125 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        reserve += msg.value;
    }
    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].code.length;
        }
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }

    function ownerOf_() public view returns (address) { return owner; }
}
